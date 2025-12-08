from ..modules.DataType import RecordedVideoData
from flask import jsonify
import glob
import os
import logging
import datetime
import re
logger = logging.getLogger("flask.app")


class SendRecordsCameraModules:
    __instance = None
    __isInitialized = False


    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    def __init__(self, videos_record_path):
        if not self.__isInitialized: 
            self.__isInitialized = True
            self.__videos_record_path = videos_record_path
    def __get_time_created_video(self, path):
        stat = os.stat(path)
        created = datetime.datetime.fromtimestamp(stat.st_ctime)

        return created.strftime("%Y-%m-%d %H:%M:%S")

    
    def __get_video_name(self, path):
         match = re.search(r"[^\\/]+$", path)
         return match[0]

    def __get_all_videos_name(self):
        videos = []
        video_paths = glob.glob(f"./src/modules/server/back_end/static/video/*.mp4")
        id = 0

        for path in video_paths:
            vid_cre_time = self.__get_time_created_video(path)
            vid_name = self.__get_video_name(path)
            vid_id = id
            vid_url = self.__videos_record_path + "/" + vid_name
            id += 1
            videos.append(RecordedVideoData(id=id, title=vid_name.replace(".mp4",""), extractedTime= vid_cre_time,
                                            videoUrl=vid_url))
        
        return videos

    def getVideoRecords(self):

        records_video = self.__get_all_videos_name()

        return jsonify(records_video)