import os
from typing import Dict

import tweepy
import yaml


class TwitterPublisher:
    creds: Dict[str, str]
    client: tweepy.Client

    def __init__(self) -> None:
        self.creds = self.set_creds()
        self.client = self.set_client()

    def set_creds(self) -> Dict[str, str]:
        """Set Twitter API keys"""
        with open(f"{os.path.expanduser('~')}/.twurlrc") as stream:
            try:
                rc = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        creds = next(iter(rc['profiles'][None].items()))[1]
        return creds

    def set_client(self) -> tweepy.Client:
        client = tweepy.Client(
            consumer_key=self.creds['consumer_key'],
            consumer_secret=self.creds['consumer_secret'],
            access_token=self.creds['token'],
            access_token_secret=self.creds['secret'],
        )
        return client

    def post_tweet(self, text: str) -> None:
        if len(text) > 280:
            raise ValueError(
                f'Tweet cannot exceed 280 characters. {len(text)}',
            )
        self.client.create_tweet(text=text)
