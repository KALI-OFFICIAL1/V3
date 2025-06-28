import aiohttp
import re
from typing import Union
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from EsproMusic.utils.formatters import time_to_seconds


class YouTubeAPI:
    def __init__(self):
        self.api_key = "AIzaSyBn2jMwMa8FA6RJM7VxJllHl5syO9K9hPg"
        self.video_url = "https://www.youtube.com/watch?v="
        self.api_base = "https://www.googleapis.com/youtube/v3"
        self.regex = r"(?:youtube\.com|youtu\.be)"

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.video_url + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset is None:
            return None
        return text[offset:offset + length]

    async def _get_video_data(self, video_id):
        url = f"{self.api_base}/videos?part=snippet,contentDetails&id={video_id}&key={self.api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if not data["items"]:
                    return None
                return data["items"][0]

    def _parse_duration(self, duration):
        import isodate
        try:
            total = isodate.parse_duration(duration).total_seconds()
            return int(total)
        except:
            return 0

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.video_url + link
        video_id = self.extract_video_id(link)
        data = await self._get_video_data(video_id)
        if not data:
            return None, None, None, None, None
        title = data["snippet"]["title"]
        thumbnail = data["snippet"]["thumbnails"]["high"]["url"]
        duration_str = data["contentDetails"]["duration"]
        duration_min = str(isodate.parse_duration(duration_str))
        duration_sec = self._parse_duration(duration_str)
        return title, duration_min, duration_sec, thumbnail, video_id

    async def title(self, link: str, videoid: Union[bool, str] = None):
        video_id = self.extract_video_id(link if not videoid else self.video_url + videoid)
        data = await self._get_video_data(video_id)
        return data["snippet"]["title"] if data else None

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        video_id = self.extract_video_id(link if not videoid else self.video_url + videoid)
        data = await self._get_video_data(video_id)
        if data:
            duration_str = data["contentDetails"]["duration"]
            return str(isodate.parse_duration(duration_str))
        return None

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        video_id = self.extract_video_id(link if not videoid else self.video_url + videoid)
        data = await self._get_video_data(video_id)
        return data["snippet"]["thumbnails"]["high"]["url"] if data else None

    async def track(self, link: str, videoid: Union[bool, str] = None):
        video_id = self.extract_video_id(link if not videoid else self.video_url + videoid)
        data = await self._get_video_data(video_id)
        if not data:
            return None, None
        title = data["snippet"]["title"]
        duration_str = data["contentDetails"]["duration"]
        duration_min = str(isodate.parse_duration(duration_str))
        thumbnail = data["snippet"]["thumbnails"]["high"]["url"]
        yturl = f"{self.video_url}{video_id}"
        return {
            "title": title,
            "link": yturl,
            "vidid": video_id,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }, video_id

    async def playlist(self, playlist_id: str, limit: int, user_id: int, videoid: Union[bool, str] = None):
        url = f"{self.api_base}/playlistItems?part=snippet&playlistId={playlist_id}&maxResults={limit}&key={self.api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                result = []
                for item in data.get("items", []):
                    vid = item["snippet"]["resourceId"]["videoId"]
                    result.append(vid)
                return result

    def extract_video_id(self, url: str):
        """
        Extract YouTube video ID from URL
        """
        pattern = (
            r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
        )
        match = re.search(pattern, url)
        return match.group(1) if match else url