from dataclasses import dataclass

@dataclass
class LogsData:
    id: str
    title: str
    description: str
    time: str
    file_path: str
    
@dataclass
class RecordedVideoData:
    id: str
    title: str
    extractedTime: str
    videoUrl: str

@dataclass
class AlertData:
    id: str
    ms: str