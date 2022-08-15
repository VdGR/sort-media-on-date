"""sort-media-on-date.py: Group media created on the same day together"""
__author__      = "Robin Van der Gucht"
__version__ = "1.0.0"

from logging import exception
import os, sys
from pathlib import Path
import subprocess
from datetime import datetime
from unittest import skip
import filetype
from dateutil import parser
import hashlib

in_dir = str(input(f"Input folder? (media/): ") or "media\\")
out_dir = str(input(f"Output folder? (out/): ") or "out\\")

FOLDER_FORMAT = "%Y/%m/%d"
errors = ""
#shutil.copy(f, os.path.join(to_dir,filename))

def printerr(string, error_log=errors):
    print(string)
    error_log += f'{string}\n'

def create_dir_if_not_exist(dir):
    #If the dir supplied does not exist creat it
    dirs = dir.split('/')
    for i, dir in enumerate(dirs):
        dir_to_create = ''.join(f"{dir}/" for dir in dirs[0:i+1])
        if not os.path.isdir(dir_to_create): 
                os.mkdir(dir_to_create)
                print(f"[+] Creating '{dir_to_create}' directory")

def get_exif_info(path):
    #Getting the absolute path
    absolute_path = os.path.join( os.getcwd(), path )
    #Executing Exiftool
    process = subprocess.Popen(["exiftool", absolute_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #Getting the output of exiftool
    out, err = process.communicate()
    #Returing the output
    try:
        return out.decode("utf-8").split("\n")
    except UnicodeDecodeError:
        #printerr(f'[!] Error with decoding for {path}')
        return None
        

def get_exif_creation_date(path):
    EXIFTOOL_DATE_TAG_VIDEOS = "Create Date"
    EXIF_DATE_FORMAT = "%Y:%m:%d %H:%M:%S"
    EXIF_DATE_FORMAT_TZ = "%Y:%m:%d %H:%M:%S%z"

    #Loop over the exiftool output and get the "Create Data tag"
    exif_data = get_exif_info(path)
    if exif_data is None: 
        #printerr(f'[!] Error no exif data for {path}')
        return None
    for l in exif_data:
        if EXIFTOOL_DATE_TAG_VIDEOS in str(l):
            # normally you will get 3 dates: Create Date, Track Create Date and Media Create Date, 
            # but we already return on the first hit
                #Create Date                     : 2010:10:10 10:10:10  ->  2010:10:10 10:10:10
                datetime_str = str(l.split(" : ")[1].strip())
                #Parse the string "2010:10:10 10:10:10" and create datetime object
                try: 
                    return datetime.strptime(datetime_str, EXIF_DATE_FORMAT)
                #Sometime the string contains a timezone
                except ValueError:
                    return datetime.strptime(datetime_str, EXIF_DATE_FORMAT_TZ)
                    

def get_hash(file):
   #programiz.com/python-programming/examples/hash-file

   h = hashlib.sha1()

   # open file for reading in binary mode
   with open(file,'rb') as file:

       # loop till the end of the file
       chunk = 0
       while chunk != b'':
           # read only 1024 bytes at a time
           chunk = file.read(1024)
           h.update(chunk)

   return h.hexdigest()

def move_file(f,f_new):
    try:
        os.rename(f, f_new)
        print(f"[+] Moving {f} to {f_new}")
    except FileExistsError:
        if get_hash(f) == get_hash(f_new):
            os.remove(f)
            printerr(f"[!] Removing '{f}'")

def main():
    #Loop over all folders/subfolders/files
    for root, subdirectories, files in os.walk(in_dir):
        for subdirectory in subdirectories:
            dir = os.path.join(root, subdirectory)

            #print(f"[+] {dir} contains {len(dir)}# files")

        for file in files:
            f = os.path.join(root, file)

            try:
                if filetype.is_image(f):
                    creation_date = get_exif_creation_date(f)
                    if creation_date is None: 
                        #If there is no exif creation date, we can check the filename for a date
                        try:
                            found_date = parser.parse(file, fuzzy=True)
                            #It find dates in names like 'imagesVF9MNS0L.jpg'???
                            if str(datetime.strftime(found_date,'%Y%m%d')) in file:
                                creation_date = found_date
                        except Exception as e:
                            #print(f"[!] {e}")
                            continue
                    if creation_date is None:
                        continue   
                    if creation_date > datetime.now():
                        #printerr(f"[!] Error {f} is older than today?")
                        continue

                    #Use the creation date to get the selected folder
                    selected_folder = os.path.join(out_dir,datetime.strftime(creation_date,FOLDER_FORMAT))
                
                    #Check if the selectd folder already exists otherwise create it
                    create_dir_if_not_exist(selected_folder)
                    #Moving the file to the selected folder
                    f_new = os.path.join(selected_folder,file)
                    move_file(f,f_new)
            
            except Exception as e:
                printerr(f"[!] Error {e}")
                continue


    f = open("errors.txt", "w")
    f.write(errors)
    f.close()

if __name__ == "__main__":
    main()