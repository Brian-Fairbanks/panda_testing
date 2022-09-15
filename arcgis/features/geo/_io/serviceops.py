from arcgis.features import Feature, FeatureSet
from arcgis.features import FeatureLayer, Table
from arcgis.geometry import Geometry
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
def _chunks(l, n):
    """yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i : i + n]


if [float(i) for i in pd.__version__.split(".")] < [1, 0, 0]:
    _look_up_types = {
        "esriFieldTypeSmallInteger": np.int32,
        "esriFieldTypeInteger": np.int32,
        "esriFieldTypeSingle": float,
        "esriFieldTypeDouble": float,
        "esriFieldTypeFloat": float,
        "esriFieldTypeString": str,
        "esriFieldTypeDate": pd.datetime,
        "esriFieldTypeOID": np.int64,
        "esriFieldTypeGeometry": object,
        "esriFieldTypeBlob": object,
        "esriFieldTypeRaster": object,
        "esriFieldTypeGUID": str,
        "esriFieldTypeGlobalID": str,
        "esriFieldTypeXML": object,
    }
else:
    from datetime import datetime as _datetime

    _look_up_types = {
        "esriFieldTypeSmallInteger": np.int32,
        "esriFieldTypeInteger": np.int32,
        "esriFieldTypeSingle": np.float64,
        "esriFieldTypeDouble": np.float64,
        "esriFieldTypeFloat": np.float64,
        "esriFieldTypeString": str,
        "esriFieldTypeDate": "<M8[us]",
        "esriFieldTypeOID": np.int64,
        "esriFieldTypeGeometry": object,
        "esriFieldTypeBlob": object,
        "esriFieldTypeRaster": object,
        "esriFieldTypeGUID": str,
        "esriFieldTypeGlobalID": str,
        "esriFieldTypeXML": object,
    }

# --------------------------------------------------------------------------
_look_up_types_old = {
    "esriFieldTypeBlob": object,
    "esriFieldTypeDate": "<M8[us]",
    "esriFieldTypeInteger": np.int32,
    "esriFieldTypeSmallInteger": np.int32,
    "esriFieldTypeDouble": float,
    "esriFieldTypeFloat": float,
    "esriFieldTypeSingle": float,
    "esriFieldTypeString": str,
    "esriFieldTypeGeometry": "O",
    "esriFieldTypeOID": np.int64,
    "esriFieldTypeGlobalID": str,
    "esriFieldTypeRaster": "O",
    "esriFieldTypeGUID": str,
    "esriFieldTypeXML": "O",
}

# --------------------------------------------------------------------------
def to_featureset(df):
    """converts a pd.DataFrame to a FeatureSet Object"""
    if hasattr(df, "spatial"):
        fs = df.spatial.__feature_set__
        return FeatureSet.from_dict(fs)
    return None


# --------------------------------------------------------------------------
def from_featureset(fset, sr=None):
    """

    Converts a FeatureSet to a pd.DataFrame

    ===============    ==============================================
    Arguments          Description
    ---------------    ----------------------------------------------
    fset               Required FeatureSet.  FeatureSet object.
    ===============    ==============================================

    return Panda's DataFrame

    """
    if isinstance(fset, FeatureSet):
        rows = []
        sr = fset.spatial_reference
        try:
            gt = fset.geometry_type.replace("esriGeometry", "")
        except:
            gt = None
        cols = [fld["name"] for fld in fset.fields]
        dt_fields = [
            fld["name"]
            for fld in fset.fields
            if ("type" in fld and fld["type"] == "esriFieldTypeDate")
            or ("fieldType" in fld and fld["fieldType"] == "esriFieldTypeDate")
        ]

        pandas_dtypes = {}
        for fld in fset.fields:
            if "type" in fld:
                pandas_dtypes[fld["name"]] = _look_up_types[fld["type"]]
            elif "fieldType" in fld:
                pandas_dtypes[fld["name"]] = _look_up_types[fld["fieldType"]]
            else:
                pandas_dtypes[fld["name"]] = "O"
        if sr is None:
            sr = {"wkid": 4326}
        for feat in fset.features:
            a = feat.attributes
            if not feat.geometry is None:
                g = feat.geometry
                g["spatialReference"] = sr
                a["SHAPE"] = Geometry(g)
            rows.append(a)
            del a, feat
        from arcgis.features import GeoAccessor, GeoSeriesAccessor

        if len(rows) > 0 and len(set(rows[0].keys()) - set(cols)) > 0:
            cols = list(rows[0].keys())
        df = pd.DataFrame(data=rows, columns=cols)

        for fld in dt_fields:
            try:
                df[fld] = pd.to_datetime(
                    df[fld] / 1000, infer_datetime_format=True, unit="s"
                )
            except:
                df[fld] = pd.to_datetime(df[fld], infer_datetime_format=True)
        if gt and not "SHAPE" in df.columns:
            df["SHAPE"] = None
        if "SHAPE" in df.columns:
            df.spatial.set_geometry("SHAPE")
            df.spatial.sr = sr
            for i in range(len(df)):
                shape = df.loc[i]["SHAPE"]
                # Check if NaN by comparing to self.
                if shape != shape:
                    df.iat[i, df.columns.get_loc("SHAPE")] = None
        if pandas_dtypes:
            try:
                return df.astype(pandas_dtypes)
            except:
                return df
        return df
    else:
        return None


# --------------------------------------------------------------------------
def from_layer(layer, query="1=1"):
    """
    Converts a Feature Service Layer to a Pandas' DataFrame

    Parameters:
     :layer: FeatureLayer or Table object.  If the object is a FeatureLayer
      the function will return a Spatial DataFrame, if the object is of
      type Table, the function will return a Pandas' DataFrame


    Usage:

    >>> from arcgis.features import FeatureLayer
    >>> mylayer = FeatureLayer(("https://sampleserver6.arcgisonline.com/arcgis/rest"
                        "/services/CommercialDamageAssessment/FeatureServer/0"))
    >>> df = from_layer(mylayer)
    >>> print(df.head())

    """
    if not layer.filter is None:
        query = layer.filter
    from arcgis.geometry import Geometry, SpatialReference

    fields = []
    records = []
    if isinstance(layer, (Table, FeatureLayer)) == False:
        raise ValueError("Invalid inputs: must be FeatureLayer or Table")
    sdf = layer.query(where=query, as_df=True)
    sdf.spatial._meta.source = layer
    if "drawingInfo" in layer.properties:
        sdf.spatial.renderer = dict(layer.properties.drawingInfo.renderer)
    else:
        sdf.spatial.renderer = dict({})
    return sdf


# ----------------------------------------------------------------------
def to_layer(df, layer, update_existing=True, add_new=False, truncate=False):
    """
    Sends the Spatial DataFrame information to a published service

    :Parameters:
     :df: Spatial DataFrame object
     :layer: Feature Layer or Table Layer object
     :update_existing: boolean -
     :add_new: boolean
     :truncate: if true, all records will be deleted and the dataframe
      records will replace the service data
    Output:
     A layer object
    """
    if not isinstance(df, (pd.DataFrame)) or not hasattr(df, "spatial"):
        raise ValueError("df must be a SpatialDatframe")
    if not isinstance(layer, (Table, FeatureLayer)):
        raise ValueError("layer must be a FeatureLayer or Table Layer")
    if truncate:
        layer.delete_features(where="1=1")
        layer.edit_features(adds=to_featureset(df).features)
    elif update_existing:
        layer.edit_features(updates=to_featureset(df).features)
    elif add_new:
        layer.edit_features(adds=to_featureset(df).features)
    return layer
