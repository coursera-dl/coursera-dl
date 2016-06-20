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
    'https://www.coursera.org/api/assets.v1?ids={id}'

OPENCOURSE_ONDEMAND_COURSE_MATERIALS = \
    'https://www.coursera.org/api/onDemandCourseMaterials.v1/?'\
        'q=slug&slug={class_name}&includes=moduleIds%2ClessonIds%2CpassableItemGroups%2CpassableItemGroupChoices%2CpassableLessonElements%2CitemIds%2Ctracks'\
        '&fields=moduleIds%2ConDemandCourseMaterialModules.v1(name%2Cslug%2Cdescription%2CtimeCommitment%2ClessonIds%2Coptional)%2ConDemandCourseMaterialLessons.v1(name%2Cslug%2CtimeCommitment%2CelementIds%2Coptional%2CtrackId)%2ConDemandCourseMaterialPassableItemGroups.v1(requiredPassedCount%2CpassableItemGroupChoiceIds%2CtrackId)%2ConDemandCourseMaterialPassableItemGroupChoices.v1(name%2Cdescription%2CitemIds)%2ConDemandCourseMaterialPassableLessonElements.v1(gradingWeight)%2ConDemandCourseMaterialItems.v1(name%2Cslug%2CtimeCommitment%2Ccontent%2CisLocked%2ClockableByItem%2CitemLockedReasonCode%2CtrackId)%2ConDemandCourseMaterialTracks.v1(passablesCount)'\
        '&showLockedItems=true'

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

WINDOWS_UNC_PREFIX = u'\\\\?\\'

#: This extension is used to save contents of supplementary instructions.
IN_MEMORY_EXTENSION = 'html'

#: This marker is added in front of a URL when supplementary instructions
#: are passed from parser to downloader. URL field fill contain the data
#: that will be stored to a file. The marker should be removed from URL
#: field first.
IN_MEMORY_MARKER = '#inmemory#'

#: These are hard limits for format (file extension) and
#: title (file name) lengths to avoid too long file names
#: (longer than 255 characters)
FORMAT_MAX_LENGTH = 20
TITLE_MAX_LENGTH = 200

#: CSS that is usen to prettify instructions
INSTRUCTIONS_HTML_INJECTION = '''
<style>
pre {
    display: block;
    margin: 20px;
    background: #424242;
    color: #fff;
    font-size: 13px;
    white-space: pre-wrap;
    padding: 9.5px;
    margin: 0 0 10px;
    border: 1px solid #ccc;
}
</style>

<script type="text/javascript" async
  src="https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML">
</script>

<script type="text/x-mathjax-config">
  MathJax.Hub.Config({
    tex2jax: {
      inlineMath: [ ['$$','$$'], ['$','$'] ],
      displayMath: [ ["\\\\[","\\\\]"] ],
      processEscapes: true
    }
  });
</script>
'''
