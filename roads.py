# from pandasgui import show
import pyproj
import pandas as pd
from shapely.geometry import Point
from shapely.ops import transform
import osmnx as ox
from osmnx import distance as dist
import networkx as nx
import matplotlib.pyplot as plt
from os.path import exists
import traceback
import numpy as np
from geopandas import GeoDataFrame
from timer import Timer
import ServerFiles as sf
from os import path
from tqdm import tqdm

logger = sf.setup_logging("roads.log")
# Setup base directory
base_dir = sf.get_base_dir()

# This really is acting more like a class than a set of functions, but I really need to look into proper class declaration for python 3 ...

stationNode = ""
roadMap = ""
bypass = False
distBuf = 10000  # 10 for testing, so everything goes much faster.  Actual data should be 10000 (~6.2 miles)


def toCrs(lat, lon):
    wgs84 = pyproj.CRS("EPSG:4326")
    local = pyproj.CRS("EPSG:2277")

    wgs84_pt = Point(lat, lon)

    project = pyproj.Transformer.from_crs(wgs84, local, always_xy=True).transform
    return transform(project, wgs84_pt)


def setStation(station):
    """
    sets a current station on the map

    Parameters
    --------------------------------
    Lat : float
        latitude of location
    Lon : float
        longituted of location

    Returns
    --------------------------------
    Nearest node id to location
    """
    global roadMap
    global stationNode
    global stationSet

    stationSet = station

    coords = station["gps"]
    station["DateIncluded"] = pd.to_datetime(station["DateIncluded"], format="%m-%d-%Y")

    point = toCrs(coords[1], coords[0])

    node = ox.nearest_nodes(roadMap, point.x, point.y)
    nodeDist = ox.nearest_nodes(roadMap, point.x, point.y, return_dist=True)

    # print("===== Station node:distance - \n", nodeDist)
    # print(point)
    # print(roadMap.nodes[node], "\n===============================\n")

    stationNode = node
    return stationNode


def distToStationFromGPS(lat, lon):
    """
    returns the distance from a passed lat lon set to a station -
    requires a station be set.  May crash if no station is set.

    Parameters
    --------------------------------
    Lat : float
        latitude of location
    Lon : float
        longituted of location

    Returns
    --------------------------------
    Float
        shortest distance along roadways between passed location and station
    """
    global stationNode

    # get the nearest network node to each point
    point = toCrs(lon, lat)

    dest_node = ox.nearest_nodes(roadMap, point.x, point.y)

    nodeDist = ox.nearest_nodes(roadMap, point.x, point.y, return_dist=True)

    # if the incident is more than .3 miles from nearest node, something is problematic
    # if nodeDist[1] > 500:
    #     return -1

    # print("===== Station node:distance - \n", nodeDist)
    # print(point)
    # print(roadMap.nodes[dest_node], "\n===============================\n")

    # dest_node = ox.nearest_nodes(roadMap, lon, lat)

    # print(station, ":", dest_node)

    try:
        # how long is our route in meters?
        # dist = ox.shortest_path(roadMap, station, dest_node, weight="length")
        dist = nx.shortest_path_length(roadMap, stationNode, dest_node, weight="length")
        # print("shortest path is:", dist)
    except:
        if stationNode == "":
            print(
                "You have likely just attempted to find the distance from a station, without first setting a station (setStation(lat,lon))"
            )
        else:
            print(
                "error getting distance between: ", stationNode, " & ", dest_node
            )  ## usually the map is to small and a connection cannot be found
            traceback.print_stack()
        return None

    distInMiles = dist * float(0.000621371)
    return distInMiles


def distToStationFromNode(dest_node, bucket, date, fullProgress=None):
    """
    returns the distance from a passed map node -
    requires a station be set.  May crash if no station is set.

    Parameters
    --------------------------------
    dest_node : str
        strin index of a node on roadMap
    (Optional) : tqdm progress bar


    Returns
    --------------------------------
    Float
        shortest distance along roadways between passed location and station
    """
    # Update overall progress bar
    if fullProgress is not None:
        fullProgress.update(1)

    # dont bother trying empty nodes
    if pd.isnull(dest_node):
        return None

    # exclude stations without ambos from med calls
    # print(bucket, stationSet["hasEMS"], end=": ")
    if bucket in ["MED"] and not stationSet["hasEMS"]:
        # print("has no ambos")
        return np.inf

    # # exclude stations without ENGs from eng calls
    if bucket in ["ENG"] and not stationSet["hasFire"]:
        #     # print("has no trucks")
        return np.inf

    # print(f"{date} : {stationSet['DateIncluded']}")
    if date < stationSet["DateIncluded"]:
        # print("DATE BEFORE ACTIVE")
        return np.inf
    try:
        # how long is our route in meters?
        dist = nx.shortest_path_length(roadMap, stationNode, dest_node, weight="length")
    except:
        if stationNode == "":
            print(
                "You have likely just attempted to find the distance from a station, without first setting a station (setStation(lat,lon))"
            )
        # else:
        # print("error getting finding path between: ", station, " & ", dest_node)
        ## usually the map is to small and a connection cannot be found
        # traceback.print_stack()
        return None

    distInMiles = dist * float(0.000621371)
    return distInMiles


# ##############################################################################################################################################
#     GDF Addition Functions
# ##############################################################################################################################################


def getPoint(point, type):
    if type not in ["ENG", "MED"]:
        return None
    if pd.isnull(point.x) | pd.isnull(point.y):
        return None
    return ox.nearest_nodes(roadMap, point.x, point.y)


def addNearestNodeToGDF(gdf):
    """
    Adds a "nearest node" column to a passed dataframe with geometries

    Parameters
    --------------------------------
    gdf : Geo DataFrame
        containing 'geometry' col for nods

    Returns
    --------------------------------
    GDF
        copy of gdf, but with an extra row for nearest node on RoadMap
    """
    tqdm.pandas(desc="Finding nearest Nodes:")

    # with tqdm(total=len(gdf.index), desc="Finding nearest Nodes:") as pbar:
    gdf["nearest node"] = gdf.progress_apply(
        lambda row: getPoint(row.geometry, row["Bucket Type"]), axis=1
    )

    return gdf


def getArrayDistToStation(df):
    """
    returns the distance to a previously set statation for a a passed dataframe
    requires a station be set.  May crash if no station is set.

    Parameters
    --------------------------------
    df : Dataframe
        should contain latitude and longitudes for each location

    Returns
    --------------------------------
    Dataframe
    """
    with tqdm(
        total=len(stationDict) * len(df.index), desc="Routing All Stations:"
    ) as stationBar:
        for curStat in stationDict:
            stationBar.update(1)
            # set station on road map
            setStation(stationDict[curStat])
            # calculate distances

            tqdm.pandas(
                desc=f"Calculating distance to {curStat}:",
                leave=False,
            )
            df[f"Distance to {curStat} in miles"] = df.progress_apply(
                lambda x: distToStationFromNode(
                    x["nearest node"],
                    x["Bucket Type"],
                    x["Earliest Time Phone Pickup AFD or EMS"],
                    stationBar,
                ),
                axis=1,
            )

    return df


def addClosestStations(df):
    import re  # make sure that we can run regular expressions.

    names = [f"Distance to {i} in miles" for i in stationDict]
    # get row name with shortest distance
    df["Closest Station"] = df[names].idxmin(axis=1)

    # get value of shortest distance, compare against .05 miles.
    df["is_walkup"] = df[names].min(axis=1) < 0.05

    def tryRegex(x):
        try:
            return re.search("(?<=Distance to )(.*)(?= in miles)", x).group(0)
        except:
            return None

    # Simplify Name
    df["Closest Station"] = df.apply(
        lambda x: tryRegex(str(x["Closest Station"])),
        axis=1,
    )
    return df


# ##############################################################################################################################################
#     Map Processing Helper Functions
# ##############################################################################################################################################
def downloadData():
    place_name = "Pflugerville, Texas, United States"
    try:
        logger.info(f"Starting download for place: {place_name} with buffer: {distBuf}")
        # buffer distance is area in meters outside of the city.
        # district can extend up to 5 miles out
        # 10000m = 6.21 miles
        G = ox.graph_from_place(place_name, buffer_dist=distBuf)
        
        # save graph to disk
        logger.info("Saving Downloaded Map ...")
        ox.save_graphml(G, path.join(base_dir, "data", "roads", "roads.graphml"))
        logger.info("Save Complete!")
        
        # return the data
        return G
    except Exception as e:
        logger.error(f"Error downloading data: {e}")
        raise



def simplifyMap(G):
    # Project the map (into the proper GPS coordinates system?)
    print(" projecting map...")
    GProj = ox.project_graph(G)

    print(" Consolidating...")
    GCon = ox.consolidate_intersections(
        GProj, rebuild_graph=True, tolerance=20, dead_ends=False
    )

    print("  Saving Simplified Map ...")
    ox.save_graphml(G, path.join(base_dir, "data", "roads", "roadsProjected.graphml"))
    print("  Save Complete!")

    return GCon


def getRoads():
    global roadMap

    roads_graphml_path = path.join(base_dir, "data", "roads", "roadsProjected.graphml")
    if not exists(roads_graphml_path):
        # final version does exists, see if partial one does.
        roads_partial_path = path.join(base_dir, "data", "roads", "roads.graphml")
        if not exists(roads_partial_path):
            print("Downloading data from the api, this may take a moment")
            G = downloadData()
        else:
            print("Found a partial file:")
            G = ox.load_graphml(roads_partial_path)
        # then prep for final data
        GCon = simplifyMap(G)
    else:
        print("Completed Map Exists, this will be quite quick")
        G = ox.load_graphml(roads_graphml_path)
        print(" projecting map...")
        GProj = ox.project_graph(G)

        print(" Consolidating...")
        GCon = ox.consolidate_intersections(
            GProj, rebuild_graph=True, tolerance=5, dead_ends=False
        )

    print("Projecting to Texas Local Map...")
    GFIPS = ox.project_graph(GCon, to_crs="epsg:2277")

    print("Map is ready for use!")

    # store and return the data
    roadMap = GFIPS
    return GFIPS


# =================================
#    Primary function called from outside
# =================================


def addRoadDistances(df):
    df["Closest Station"] = None
    for i in range(1, 10):
        df[f"Distance to S0{i} in miles"] = None
    # toggle the below return to bypass (skip) this section
    if bypass:
        df["is_walkup"] = None
        return df

    import re
    import getData as data

    global stationDict
    stationDict = data.getStations()

    # add geometry to newly created GeoDataFrame, and convert to FIPS
    geometry = [Point(xy) for xy in zip(df["X-Long"], df["Y_Lat"])]
    gdf = GeoDataFrame(df, crs="EPSG:4326", geometry=geometry)
    gdf = gdf.to_crs(2277)

    # Load road map data
    getRoads()
    print("Roads Gathered:\n\n")

    gdf = addNearestNodeToGDF(gdf)

    print("Nearest Nodes Identified:\n\n")

    gdf = getArrayDistToStation(gdf)

    # show(gdf)

    # these dont really mean anything without the context of the graph, so drop them off... and then garbage collect gdf
    df = pd.DataFrame(gdf.drop(columns=["geometry", "nearest node"]))
    gdf = None
    # add Closest Station column
    df = addClosestStations(df)

    # remove infininity number applied to invalid Location_At_Assign_Time
    df.replace(np.inf, None, inplace=True)
    return df


################################
# ==================================================================
#
#
# Testing Code: will only run when this file is called directly.
# ==================================================================
################################


def testMap():
    # load road data
    roads = getRoads()

    print("graph is complete.  Setting Station Location")

    setStation(stationDict["S1"])

    print("finding distances:")
    # gps points to 800 Cheyenne Valley Cove, Round Rock, TX 78664.  Distance is off by ~5%
    # (7659.590000000004), but google claims 8.0km
    dist = distToStationFromGPS(30.496659877487765, -97.60270496406959)
    print("Distance is ", dist)

    print("Distances Calculated.  Opening view.")
    # plot graph
    fig, ax = ox.plot_graph(roads)
    plt.tight_layout()


def testNearestNodes():

    import loadTestFile

    df = loadTestFile.get()
    # df = df.head(50)
    # remove data not useful for the testing
    limit = [
        "Y_Lat",
        "X-Long",
    ]
    # df = df[limit]

    geoTime = Timer("Generating Points")
    geoTime.start()

    geometry = [Point(xy) for xy in zip(df["X-Long"], df["Y_Lat"])]
    gdf = GeoDataFrame(df, crs="EPSG:4326", geometry=geometry)

    geoTime.stop()

    ##
    t1 = Timer()
    t1.start()
    gdf = gdf.to_crs(2277)
    t1.end()

    t2 = Timer("Load Map")
    t2.start()
    getRoads()
    t2.end()

    t3 = Timer("Add Nearest Node to GDF")
    t3.start()
    # add_nearest_node_to_gdf(gdf, roads)
    gdf = addNearestNodeToGDF(gdf)
    t3.end()

    t4 = Timer("Finding Distance to Station")
    t4.start()
    gdf = getArrayDistToStation(gdf)
    t4.end()

    show(gdf)


def testStandAlone():
    import loadTestFile
    import utils

    df = loadTestFile.get()
    df = df.head(150)
    df = utils.addUnitType(df)
    df = utils.addBucketType(df)
    gdf = addRoadDistances(df)
    show(gdf)


def main():
    # testMap()
    # testNearestNodes()
    testStandAlone()


if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
    main()
