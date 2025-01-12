import pandas as pd

# from pandasgui import show

from tkinter import *
from tkinter import messagebox
from tkinter.filedialog import askopenfile, askopenfilenames

import analyzefire as af
import preprocess as pp
import numpy as np

from Database import SQLDatabase

db = SQLDatabase()
from Email_Report import get_and_run_reports


fileArray = {}
ws = None


def createGui():
    ws = Tk()
    ws.title("Fire/EMS Management")
    ws.geometry("600x200")

    ws.columnconfigure(0, weight=1)
    ws.rowconfigure(1, weight=1)

    #     Frame for file dialog
    # =========================================================================================================================
    frame1 = LabelFrame(ws, text="File Selection")
    frame1.grid(row=0, column=0, columnspan=4, sticky=("ew"))

    frame1.columnconfigure(0, weight=1)

    addFileLabel = Label(frame1, text="Add Files to List")
    addFileLabel.grid(row=0, column=0, padx=10)

    addFileBtn = Button(frame1, text="Choose File", command=lambda: addFiles())
    addFileBtn.grid(row=0, column=1)

    analyzeButton = Button(frame1, text="Analyze Data", command=lambda: guiAnalyze())
    analyzeButton.grid(row=0, column=2)

    rawInsert = Button(frame1, text="Insert Raw Data", command=lambda: insertRaw())
    rawInsert.grid(row=1, column=2)

    global fileList
    fileList = Listbox(frame1, height=5)
    fileList.grid(row=3, column=0, columnspan=4, sticky=("ew"))

    linkData = Button(
        ws, text="Update Dependency Tables", command=lambda: update_dependency_tables()
    )
    linkData.grid(row=1, column=0, columnspan=3)

    run_Reports = Button(ws, text="Email Reports", command=lambda: runReports())
    run_Reports.grid(row=2, column=0, columnspan=3)

    return ws


# TODO - Add ability to drag and drop files directly onto this list


def guiAnalyze():
    for file in fileArray:
        fileDF = af.analyzeFire(fileArray[file])
        # ----------------
        # Write to Database
        # ----------------
        from Database import SQLDatabase
        
        data_source = fileDF.loc[0, "Data_Source"]

        db = SQLDatabase()
        # db.insertDF(fileDF)
        db.new_insert_DF(fileDF, data_source)

    return None


def runReports():
    get_and_run_reports()


def update_dependency_tables():
    from datetime import datetime, timedelta

    today = datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    one_month_ago = today - timedelta(days=30)
    one_month_ago = one_month_ago.replace(hour=0, minute=0, second=0, microsecond=0)
    print("Updating Fire-EMS Link Table")
    db.RunFireEMSLink(one_month_ago)
    print(" - Done Updating!")
    print("Updating Truck Concurrency Table")
    db.RunConcurrencyUpdate(one_month_ago, today)
    print(" - Done Updating!")


def readRaw(filePath):
    excel_filename = r"{}".format(filePath)
    # read the file
    df = pd.read_excel(excel_filename)

    if "Ph_PU_Time" in df.columns or "Ph PU Time" in df.columns:
        fileType = "ems" 
        pp.scrub_raw_ems(df) 
    else:
        fileType = "fire"

        df, non_esd_records = pp.split_esd_records(df)
        df = pp.revert_fire_format(df)
        # Dump non_esd records if they exist
        try:
            if len(non_esd_records.index) != 0:
                pp.dump_to_database(non_esd_records, fileType)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"Error Dumping Raw Data: {e}\nTraceback: {tb}")
            exit()

    df = df.replace("-", np.nan)

    renames = {"ESD02_Record_Daily": "ESD02_Record",
               "ESD02_Record_New_Daily": "ESD02_Record",
               "ESD02_Record_New": "ESD02_Record"}
    df = df.rename(columns=renames, errors="ignore")

    return df, fileType


def insertRaw():
    for file in fileArray.keys():  # keys should just be filepath+name
        try:
            df, filetype = readRaw(file)
            # TEMP: FIX THIS IN SCHEMAS - remove latitude and longitude for fire
            if filetype == "fire":
                df = df.drop(["Longitude_At_Assign_Time","Latitude_At_Assign_Time"], axis=1, errors="ignore")
            dumpRawData(df, filetype)

        except ValueError:
            messagebox.showerror("Invalid File", "The loaded file is invalid")
            return None
        except FileNotFoundError:
            messagebox.showerror("Invalid File", "No such file as {excel_filename}")
            return None


def remove_completed_files():
    print("Clearing completed Files from FileArray")
    fileArray.clear()


def addFiles(files=None):
    if files == None:
        files = askopenfilenames(parent=ws, title="Choose Files")
    # ensure unique items in list
    for file in files:
        # if ws exists (gui is actually runnng) temporarily add to file list to show that things are running
        if ws:
            fileList.insert("end", file)

        # then check if file is valid, read it, and hold onto its DF
        if not file in fileArray.keys():
            try:
                excel_filename = r"{}".format(file)
                # read the file
                fileArray[file] = pp.preprocess(pd.read_excel(excel_filename))

            except ValueError:
                messagebox.showerror("Invalid File", "The loaded file is invalid")
                return None
            except FileNotFoundError:
                messagebox.showerror("Invalid File", "No such file as {excel_filename}")
                return None

    # Silent run Gatekeeping
    if not ws:
        return

    # reprint list
    fileList.delete(0, "end")
    for file in fileArray.keys():
        fileList.insert("end", file)


def dumpRawData(df, type):
    print("Dumping Raw Data to Database")
    db.UpsertRaw(df, type)


def run():
    ws = createGui()
    ws.mainloop()


if __name__ == "__main__":
    ws = createGui()
    ws.mainloop()
