# @Author: aero
# @Date:   2018-10-17T14:56:06+08:00
# @Email:  neuhutao@gmail.com
# @Filename: ModelsimImportProjectScriptsGenerator.py
# @Last modified by:   aero
# @Last modified time: 2018-10-17T15:30:43+08:00
#
# This python script will walk through the Modelsim folders
# and generate a .do file to
# build the corresponding directory structure and add files in the project.
import os
SrcFolder = "src" #default src code folder
ProjectName = "RISCV_TEST"
DoFile = open("import.do","w")
DoFile.writelines("project open " + ProjectName + "\nproject addfolder " + SrcFolder + " \n")
path = "./" + SrcFolder
folder = ""
def getFileType(filename):
    """Short summary.
    Get file type code for Modelsim via suffix name of the file
    Parameters
    ----------
    filename : String
        The full name of a file.

    Returns
    -------
    String
        File type code for Modelsim.
    """
    TypeStr = os.path.splitext(filename)[-1][1:]
    if TypeStr == "sv":
        return " SystemVerilog "
    elif TypeStr == "v":
        return " verilog "
    elif TypeStr == "vhdl":
        return " vhdl "
    elif TypeStr == " do ":
        return " do "
    else:
        return " txt "
#First walk to build directory structures
for i in os.walk(path):
    dir = str(os.path.relpath(i[0]))
    dir = dir.replace("/","_")
    for folder in i[1]:
        strfolder = str(dir) + "_" +str(folder)
        DoFile.writelines("project " + " addfolder " + strfolder.replace("/","_") + " " + dir + " " +  "\n" )
#
for i in os.walk(path):
    dir = str(os.path.relpath(i[0]))
    dir.replace("/","_")
    level = level + 1

    for file in i[2]:
        DoFile.writelines("project addfile " + "./" + str(os.path.relpath(i[0])) + "/" + file + getFileType(file) + dir.replace("/","_") +"\n" )
