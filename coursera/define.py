# -*- coding: utf-8 -*-

"""
This module defines the global constants.
"""

import os
import getpass
import tempfile

COURSERA_URL = 'https://www.coursera.org'
AUTH_URL = 'https://accounts.coursera.org/api/v1/login'
AUTH_URL_V3 = 'https://www.coursera.org/api/login/v3'
CLASS_URL = 'https://class.coursera.org/{class_name}'
OPENCOURSE_CONTENT_URL = 'https://www.coursera.org/api/opencourse.v1/course/{class_name}'
OPENCOURSE_VIDEO_URL = 'https://www.coursera.org/api/opencourse.v1/video/{video_id}'
OPENCOURSE_SUPPLEMENT_URL = 'https://www.coursera.org/api/onDemandSupplements.v1/'\
    '{course_id}~{element_id}?includes=asset&fields=openCourseAssets.v1%28typeName%29,openCourseAssets.v1%28definition%29'
OPENCOURSE_PROGRAMMING_ASSIGNMENTS_URL = \
    'https://www.coursera.org/api/onDemandProgrammingLearnerAssignments.v1/{course_id}~{element_id}?fields=submissionLearnerSchema'

# These are ids that are present in <asset> tag in assignment text:
#
# <asset id=\"yeJ7Q8VAEeWPRQ4YsSEORQ\"
#        name=\"statement-pca\"
#        extension=\"pdf\"
#        assetType=\"generic\"/>
#
# Sample response:
#
# {
#   "elements": [
#     {
#       "id": "yeJ7Q8VAEeWPRQ4YsSEORQ",
#       "url": "<some url>",
#       "expires": 1454371200000
#     }
#   ],
#   "paging": null,
#   "linked": null
# }
OPENCOURSE_ASSET_URL = \
    'https://www.coursera.org/api/assetUrls.v1?ids={ids}'

# These ids are provided in lecture json:
#
# {
#   "id": "6ydIh",
#   "name": "Введение в теорию игр",
#   "elements": [
#     {
#       "id": "ujNfj",
#       "name": "Что изучает теория игр?",
#       "content": {
#         "typeName": "lecture",
#         "definition": {
#           "duration": 536000,
#           "videoId": "pGNiQYo-EeWNvA632PIn3w",
#           "optional": false,
#           "assets": [
#             "giAxucdaEeWJTQ5WTi8YJQ@1"
#           ]
#         }
#       },
#       "slug": "chto-izuchaiet-tieoriia-ighr",
#       "timeCommitment": 536000
#     }
#   ],
#   "slug": "vviedieniie-v-tieoriiu-ighr",
#   "timeCommitment": 536000,
#   "optional": false
# }
#
# Sample response:
#
# {
#   "elements": [
#     {
#       "id": "giAxucdaEeWJTQ5WTi8YJQ",
#       "typeName": "asset",
#       "definition": {
#         "name": "",
#         "assetId": "Vq8hwsdaEeWGlA7xclFASw"
#       }
#     }
#   ],
#   "paging": null,
#   "linked": null
# }
OPENCOURSE_ASSETS_URL = \
    'https://www.coursera.org/api/openCourseAssets.v1/{id}'

# These asset ids are ids returned from OPENCOURSE_ASSETS_URL request:
# See example above.
#
# Sample response:
#
# {
#   "elements": [
#     {
#       "id": "Vq8hwsdaEeWGlA7xclFASw",
#       "name": "1_Strategic_Interactions.pdf",
#       "typeName": "generic",
#       "url": {
#         "url": "<some url>",
#         "expires": 1454371200000
#       }
#     }
#   ],
#   "paging": null,
#   "linked": null
# }
OPENCOURSE_API_ASSETS_V1_URL = \
    'https://www.coursera.org/api/assets.v1/{id}'


ABOUT_URL = ('https://api.coursera.org/api/catalog.v1/courses?'
             'fields=largeIcon,photo,previewLink,shortDescription,smallIcon,'
             'smallIconHover,universityLogo,universityLogoSt,video,videoId,'
             'aboutTheCourse,targetAudience,faq,courseSyllabus,courseFormat,'
             'suggestedReadings,instructor,estimatedClassWorkload,'
             'aboutTheInstructor,recommendedBackground,subtitleLanguagesCsv&'
             'q=search&query={class_name}')

AUTH_REDIRECT_URL = ('https://class.coursera.org/{class_name}'
                     '/auth/auth_redirector?type=login&subtype=normal')

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# define a per-user cache folder
if os.name == "posix":  # pragma: no cover
    import pwd
    _USER = pwd.getpwuid(os.getuid())[0]
else:
    _USER = getpass.getuser()

PATH_CACHE = os.path.join(tempfile.gettempdir(), _USER + "_coursera_dl_cache")
PATH_COOKIES = os.path.join(PATH_CACHE, 'cookies')
