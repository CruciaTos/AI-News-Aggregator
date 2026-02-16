"""YouTube Data API client stub.

This file contains method signatures only and must be implemented with
proper authentication and pagination logic later.
"""


class YouTubeClient:
    """Client stub for YouTube Data API interactions."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def list_channel_videos(self, channel_id: str, max_results: int = 50):
        """Return a list of video metadata for a channel (stub)."""
        raise NotImplementedError("list_channel_videos is a scaffold stub")

    def get_video_metadata(self, video_id: str):
        """Return metadata for a single video (stub)."""
        raise NotImplementedError("get_video_metadata is a scaffold stub")
