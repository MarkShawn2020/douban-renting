from enum import Enum


class CrawlErrors(str, Enum):

    ResponseNot200: "ResponseNot200"
    ResponseNotJson: "ResponseNotJson"
    ResponseNoTargetItems: "ResponseNoTargetItems"
