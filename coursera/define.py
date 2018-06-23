# -*- coding: utf-8 -*-

"""
This module defines the global constants.
"""

import os
import getpass
import tempfile


HTTP_FORBIDDEN = 403

COURSERA_URL = 'https://api.coursera.org'
AUTH_URL = 'https://accounts.coursera.org/api/v1/login'
AUTH_URL_V3 = 'https://api.coursera.org/api/login/v3'
CLASS_URL = 'https://class.coursera.org/{class_name}'

# The following link is left just for illustrative purposes:
# https://api.coursera.org/api/courses.v1?fields=display%2CpartnerIds%2CphotoUrl%2CstartDate%2Cpartners.v1(homeLink%2Cname)&includes=partnerIds&q=watchlist&start=0
# Reply is as follows:
# {
#     "elements": [
#         {
#             "courseType": "v1.session",
#             "name": "Computational Photography",
#             "id": "v1-87",
#             "slug": "compphoto"
#         }
#     ],
#     "paging": {
#         "next": "100",
#         "total": 154
#     },
#     "linked": {}
# }
OPENCOURSE_LIST_COURSES = 'https://api.coursera.org/api/courses.v1?q=watchlist&start={start}'

# The following link is left just for illustrative purposes:
# https://api.coursera.org/api/memberships.v1?fields=courseId,enrolledTimestamp,grade,id,lastAccessedTimestamp,onDemandSessionMembershipIds,onDemandSessionMemberships,role,v1SessionId,vc,vcMembershipId,courses.v1(courseStatus,display,partnerIds,photoUrl,specializations,startDate,v1Details,v2Details),partners.v1(homeLink,name),v1Details.v1(sessionIds),v1Sessions.v1(active,certificatesReleased,dbEndDate,durationString,hasSigTrack,startDay,startMonth,startYear),v2Details.v1(onDemandSessions,plannedLaunchDate,sessionsEnabledAt),specializations.v1(logo,name,partnerIds,shortName)&includes=courseId,onDemandSessionMemberships,vcMembershipId,courses.v1(partnerIds,specializations,v1Details,v2Details),v1Details.v1(sessionIds),v2Details.v1(onDemandSessions),specializations.v1(partnerIds)&q=me&showHidden=true&filter=current,preEnrolled
# Sample reply:
# {
#     "elements": [
#         {
#             id: "4958~bVgqTevEEeWvGQrWsIkLlw",
#             userId: 4958,
#             courseId: "bVgqTevEEeWvGQrWsIkLlw",
#             role: "LEARNER"
#         },
#     ],
#     "paging": null,
#     "linked": {
#         "courses.v1": [
#             {
#                 "id": "0w0JAG9JEeSp0iIAC12Jpw",
#                 "slug": "computational-neurosciencecompneuro",
#                 "courseType": "v2.ondemand",
#                 "name": "Computational Neuroscience"
#             }
#         ]
#     }
# }
OPENCOURSE_MEMBERSHIPS = 'https://api.coursera.org/api/memberships.v1?includes=courseId,courses.v1&q=me&showHidden=true&filter=current,preEnrolled'
OPENCOURSE_ONDEMAND_LECTURE_VIDEOS_URL = \
    'https://api.coursera.org/api/onDemandLectureVideos.v1/'\
    '{course_id}~{video_id}?includes=video&'\
    'fields=onDemandVideos.v1(sources%2Csubtitles%2CsubtitlesVtt%2CsubtitlesTxt)'
OPENCOURSE_SUPPLEMENT_URL = 'https://api.coursera.org/api/onDemandSupplements.v1/'\
    '{course_id}~{element_id}?includes=asset&fields=openCourseAssets.v1%28typeName%29,openCourseAssets.v1%28definition%29'
OPENCOURSE_PROGRAMMING_ASSIGNMENTS_URL = \
    'https://api.coursera.org/api/onDemandProgrammingLearnerAssignments.v1/{course_id}~{element_id}?fields=submissionLearnerSchema'
OPENCOURSE_PROGRAMMING_IMMEDIATE_INSTRUCTIOINS_URL = \
    'https://api.coursera.org/api/onDemandProgrammingImmediateInstructions.v1/{course_id}~{element_id}'
OPENCOURSE_REFERENCES_POLL_URL = \
    "https://api.coursera.org/api/onDemandReferences.v1/?courseId={course_id}&q=courseListed&fields=name%2CshortId%2Cslug%2Ccontent&includes=assets"
OPENCOURSE_REFERENCE_ITEM_URL = \
    "https://api.coursera.org/api/onDemandReferences.v1/?courseId={course_id}&q=shortId&shortId={short_id}&fields=name%2CshortId%2Cslug%2Ccontent&includes=assets"

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
    'https://api.coursera.org/api/assetUrls.v1?ids={ids}'

# Sample response:
#  "linked": {
#    "openCourseAssets.v1": [
#      {
#        "typeName": "asset",
#        "definition": {
#          "assetId": "fytYX5rYEeedWRLokafKRg",
#          "name": "Lecture slides"
#        },
#        "id": "j6g7VZrYEeeUVgpv-dYMig"
#      }
#    ]
#  }
OPENCOURSE_ONDEMAND_LECTURE_ASSETS_URL = \
    'https://api.coursera.org/api/onDemandLectureAssets.v1/'\
    '{course_id}~{video_id}/?includes=openCourseAssets'

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
    'https://api.coursera.org/api/openCourseAssets.v1/{id}'

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
    'https://api.coursera.org/api/assets.v1?ids={id}'

OPENCOURSE_ONDEMAND_COURSE_MATERIALS = \
    'https://api.coursera.org/api/onDemandCourseMaterials.v1/?'\
    'q=slug&slug={class_name}&includes=moduleIds%2ClessonIds%2CpassableItemGroups%2CpassableItemGroupChoices%2CpassableLessonElements%2CitemIds%2Ctracks'\
    '&fields=moduleIds%2ConDemandCourseMaterialModules.v1(name%2Cslug%2Cdescription%2CtimeCommitment%2ClessonIds%2Coptional)%2ConDemandCourseMaterialLessons.v1(name%2Cslug%2CtimeCommitment%2CelementIds%2Coptional%2CtrackId)%2ConDemandCourseMaterialPassableItemGroups.v1(requiredPassedCount%2CpassableItemGroupChoiceIds%2CtrackId)%2ConDemandCourseMaterialPassableItemGroupChoices.v1(name%2Cdescription%2CitemIds)%2ConDemandCourseMaterialPassableLessonElements.v1(gradingWeight)%2ConDemandCourseMaterialItems.v1(name%2Cslug%2CtimeCommitment%2Ccontent%2CisLocked%2ClockableByItem%2CitemLockedReasonCode%2CtrackId)%2ConDemandCourseMaterialTracks.v1(passablesCount)'\
    '&showLockedItems=true'

OPENCOURSE_ONDEMAND_COURSE_MATERIALS_V2 = \
    'https://api.coursera.org/api/onDemandCourseMaterials.v2/?q=slug&slug={class_name}'\
    '&includes=modules%2Clessons%2CpassableItemGroups%2CpassableItemGroupChoices%2CpassableLessonElements%2Citems%2Ctracks%2CgradePolicy&'\
    '&fields=moduleIds%2ConDemandCourseMaterialModules.v1(name%2Cslug%2Cdescription%2CtimeCommitment%2ClessonIds%2Coptional%2ClearningObjectives)%2ConDemandCourseMaterialLessons.v1(name%2Cslug%2CtimeCommitment%2CelementIds%2Coptional%2CtrackId)%2ConDemandCourseMaterialPassableItemGroups.v1(requiredPassedCount%2CpassableItemGroupChoiceIds%2CtrackId)%2ConDemandCourseMaterialPassableItemGroupChoices.v1(name%2Cdescription%2CitemIds)%2ConDemandCourseMaterialPassableLessonElements.v1(gradingWeight%2CisRequiredForPassing)%2ConDemandCourseMaterialItems.v2(name%2Cslug%2CtimeCommitment%2CcontentSummary%2CisLocked%2ClockableByItem%2CitemLockedReasonCode%2CtrackId%2ClockedStatus%2CitemLockSummary)%2ConDemandCourseMaterialTracks.v1(passablesCount)'\
    '&showLockedItems=true'

OPENCOURSE_ONDEMAND_COURSES_V1 = \
    'https://api.coursera.org/api/onDemandCourses.v1?q=slug&slug={class_name}&'\
    'includes=instructorIds%2CpartnerIds%2C_links&'\
    'fields=brandingImage%2CcertificatePurchaseEnabledAt%2Cpartners.v1(squareLogo%2CrectangularLogo)%2Cinstructors.v1(fullName)%2CoverridePartnerLogos%2CsessionsEnabledAt%2CdomainTypes%2CpremiumExperienceVariant%2CisRestrictedMembership'

ABOUT_URL = ('https://api.coursera.org/api/catalog.v1/courses?'
             'fields=largeIcon,photo,previewLink,shortDescription,smallIcon,'
             'smallIconHover,universityLogo,universityLogoSt,video,videoId,'
             'aboutTheCourse,targetAudience,faq,courseSyllabus,courseFormat,'
             'suggestedReadings,instructor,estimatedClassWorkload,'
             'aboutTheInstructor,recommendedBackground,subtitleLanguagesCsv&'
             'q=search&query={class_name}')

AUTH_REDIRECT_URL = ('https://class.coursera.org/{class_name}'
                     '/auth/auth_redirector?type=login&subtype=normal')

# Sample URL:
#
# https://api.coursera.org/api/onDemandPeerAssignmentInstructions.v1/?q=latest&userId=4958&courseId=RcnRZHHtEeWxvQr3acyajw&itemId=2yTvX&includes=gradingMetadata%2CreviewSchemas%2CsubmissionSchemas&fields=instructions%2ConDemandPeerAssignmentGradingMetadata.v1(requiredAuthoredReviewCount%2CisMentorGraded%2CassignmentDetails)%2ConDemandPeerReviewSchemas.v1(reviewSchema)%2ConDemandPeerSubmissionSchemas.v1(submissionSchema)
#
# Sample response:
#
# {
#   "elements": [
#     {
#       "instructions": {
#         "introduction": {
#           "typeName": "cml",
#           "definition": {
#             "dtdId": "assess/1",
#             "value": "<co-content><text>Ваше первое задание заключается в установке Python и библиотек..</text></li></list></co-content>"
#           }
#         },
#         "sections": [
#           {
#             "typeId": "unknown",
#             "title": "Review criteria",
#             "content": {
#               "typeName": "cml",
#               "definition": {
#                 "dtdId": "assess/1",
#                 "value": "<co-content><text>В результате работы вы установите на компьютер Python и библиотеки, необходимые для дальнейшего прохождения курса..</text></co-content>"
#               }
#             }
#           }
#         ]
#       },
#       "id": "4958~RcnRZHHtEeWxvQr3acyajw~2yTvX~8x7Qhs66EeW2Tw715xhIPQ@13"
#     }
#   ],
#   "paging": {},
#   "linked": {
#     "onDemandPeerSubmissionSchemas.v1": [
#       {
#         "submissionSchema": {
#           "parts": [
#             {
#               "details": {
#                 "typeName": "fileUpload",
#                 "definition": {
#                   "required": false
#                 }
#               },
#               "id": "_fcfP3bPT5W4pkfkshmUAQ",
#               "prompt": {
#                 "typeName": "cml",
#                 "definition": {
#                   "dtdId": "assess/1",
#                   "value": "<co-content><text>Загрузите скриншот №1.</text></co-content>"
#                 }
#               }
#             },
#             {
#               "details": {
#                 "typeName": "fileUpload",
#                 "definition": {
#                   "required": false
#                 }
#               },
#               "id": "92ea4b4e-3492-41eb-ee32-2624ee807bd3",
#               "prompt": {
#                 "typeName": "cml",
#                 "definition": {
#                   "dtdId": "assess/1",
#                   "value": "<co-content><text>Загрузите скриншот №2.</text></co-content>"
#                 }
#               }
#             }
#           ]
#         },
#         "id": "4958~RcnRZHHtEeWxvQr3acyajw~2yTvX~8x7Qhs66EeW2Tw715xhIPQ@13"
#       }
#     ],
#     "onDemandPeerAssignmentGradingMetadata.v1": [
#       {
#         "assignmentDetails": {
#           "typeName": "phased",
#           "definition": {
#             "receivedReviewCutoffs": {
#               "count": 3
#             },
#             "passingFraction": 0.8
#           }
#         },
#         "requiredAuthoredReviewCount": 3,
#         "isMentorGraded": false,
#         "id": "4958~RcnRZHHtEeWxvQr3acyajw~2yTvX~8x7Qhs66EeW2Tw715xhIPQ@13"
#       }
#     ],
#     "onDemandPeerReviewSchemas.v1": []
#   }
# }
#
# This URL is used to retrieve "phasedPeer" typename instructions' contents
OPENCOURSE_PEER_ASSIGNMENT_INSTRUCTIONS = (
    'https://api.coursera.org/api/onDemandPeerAssignmentInstructions.v1/?'
    'q=latest&userId={user_id}&courseId={course_id}&itemId={element_id}&'
    'includes=gradingMetadata%2CreviewSchemas%2CsubmissionSchemas&'
    'fields=instructions%2ConDemandPeerAssignmentGradingMetadata.v1(requiredAuthoredReviewCount%2CisMentorGraded%2CassignmentDetails)%2ConDemandPeerReviewSchemas.v1(reviewSchema)%2ConDemandPeerSubmissionSchemas.v1(submissionSchema)')

#POST_OPENCOURSE_API_QUIZ_SESSION = 'https://api.coursera.org/api/opencourse.v1/user/4958/course/text-mining/item/7OQHc/quiz/session'
# Sample response:
#
# {
#   "contentResponseBody": {
#     "session": {
#       "id": "opencourse~bVgqTevEEeWvGQrWsIkLlw:4958:BiNDdOvPEeWAkwqbKEEh3w@13:1468773901987@1",
#       "open": true
#     }
#   },
#   "itemProgress": {
#     "contentVersionedId": "BiNDdOvPEeWAkwqbKEEh3w@13",
#     "timestamp": 1468774458435,
#     "progressState": "Started"
#   }
# }
POST_OPENCOURSE_API_QUIZ_SESSION = 'https://api.coursera.org/api/opencourse.v1/user/{user_id}/course/{class_name}/item/{quiz_id}/quiz/session'

#POST_OPENCOURSE_API_QUIZ_SESSION_GET_STATE = 'https://api.coursera.org/api/opencourse.v1/user/4958/course/text-mining/item/7OQHc/quiz/session/opencourse~bVgqTevEEeWvGQrWsIkLlw:4958:BiNDdOvPEeWAkwqbKEEh3w@13:1468773901987@1/action/getState?autoEnroll=false'
# Sample response:
#
# {
#   "contentResponseBody": {
#     "return": {
#       "questions": [
#         {
#           "id": "89424f6873744b5c0b92da2936327bb4",
#           "question": {
#             "type": "mcq"
#           },
#           "variant": {
#             "definition": {
#               "prompt": {
#                 "typeName": "cml",
#                 "definition": {
#                   "dtdId": "assess/1",
#                   "value": "<co-content><text hasMath=\"true\">You are given a unigram language model $$\\theta$$ distributed over a vocabulary set $$V$$ composed of <strong>only</strong> 4 words: “the”, “machine”, “learning”, and “data”. The distribution of $$\\theta$$ is given in the table below:</text><table rows=\"5\" columns=\"2\"><tr><th><text>$$w$$</text></th><th><text>$$P(w|\\theta)$$</text></th></tr><tr><td><text>machine</text></td><td><text>0.1</text></td></tr><tr><td><text>learning</text></td><td><text>0.2</text></td></tr><tr><td><text>data</text></td><td><text>0.3</text></td></tr><tr><td><text>the</text></td><td><text>0.4</text></td></tr></table><text hasMath=\"true\"> $$P(\\text{“machine learning”}|\\theta) = $$</text></co-content>"
#                 }
#               },
#               "options": [
#                 {
#                   "id": "717bd78dec2b817bed4b2d6096cbc9fc",
#                   "display": {
#                     "typeName": "cml",
#                     "definition": {
#                       "dtdId": "assess/1",
#                       "value": "<co-content><text>0.004</text></co-content>"
#                     }
#                   }
#                 },
#                 {
#                   "id": "a06c614cbb15b4e54212296b16fc4e62",
#                   "display": {
#                     "typeName": "cml",
#                     "definition": {
#                       "dtdId": "assess/1",
#                       "value": "<co-content><text>0.2</text></co-content>"
#                     }
#                   }
#                 },
#                 {
#                   "id": "029fe0fee932d6ad260f292dd05dc5c9",
#                   "display": {
#                     "typeName": "cml",
#                     "definition": {
#                       "dtdId": "assess/1",
#                       "value": "<co-content><text>0.3</text></co-content>"
#                     }
#                   }
#                 },
#                 {
#                   "id": "b6af6403d4ddde3b1e58599c12b6397a",
#                   "display": {
#                     "typeName": "cml",
#                     "definition": {
#                       "dtdId": "assess/1",
#                       "value": "<co-content><text>0.02</text></co-content>"
#                     }
#                   }
#                 }
#               ]
#             },
#             "detailLevel": "Full"
#           },
#           "weightedScoring": {
#             "maxScore": 1
#           },
#           "isSubmitAllowed": true
#         }
#       ],
#       "evaluation": null
#     }
#   },
#   "itemProgress": {
#     "contentVersionedId": "BiNDdOvPEeWAkwqbKEEh3w@13",
#     "timestamp": 1468774458894,
#     "progressState": "Started"
#   }
# }
#
POST_OPENCOURSE_API_QUIZ_SESSION_GET_STATE = 'https://api.coursera.org/api/opencourse.v1/user/{user_id}/course/{class_name}/item/{quiz_id}/quiz/session/{session_id}/action/getState?autoEnroll=false'

#POST_OPENCOURSE_ONDEMAND_EXAM_SESSIONS = 'https://api.coursera.org/api/onDemandExamSessions.v1/-N44X0IJEeWpogr5ZO8qxQ~YV0W4~10!~1467462079068/actions?includes=gradingAttempts'
# Sample response:
#
# {
#   "elements": [
#     {
#       "id": 0,
#       "result": {
#         "questions": [
#           {
#             "id": "8uUpMzm_EeaetxLgjw7H8Q@0",
#             "question": {
#               "type": "mcq"
#             },
#             "variant": {
#               "definition": {
#                 "prompt": {
#                   "typeName": "cml",
#                   "definition": {
#                     "dtdId": "assess/1",
#                     "value": "<co-content><text>\n\nSuppose you’d like to perform nearest neighbor search from the following set of houses:</text><table rows=\"5\" columns=\"4\"><tr><td><text>\n\n\n\n\n\n</text></td><td><text>\n\n\nPrice (USD)</text></td><td><text>\n\n\nNumber of rooms</text></td><td><text>\n\n\nLot size (sq. ft.)</text></td></tr><tr><td><text>\n\n\nHouse 1</text></td><td><text>\n\n\n500000</text></td><td><text>\n\n\n3</text></td><td><text>\n\n\n1840</text></td></tr><tr><td><text>\n\n\nHouse 2</text></td><td><text>\n\n\n350000</text></td><td><text>\n\n\n2</text></td><td><text>\n\n\n1600</text></td></tr><tr><td><text>House 3</text></td><td><text>\n\n600000</text></td><td><text>\n\n4</text></td><td><text>\n\n2000</text></td></tr><tr><td><text>House 4</text></td><td><text>\n400000</text></td><td><text>\n2</text></td><td><text>\n1900</text></td></tr></table><text>\n\nSince the features come in wildly different scales, you decide to use scaled Euclidean distances. Choose the set of weights a_i (as presented in the video lecture) that properly incorporates the relative amount of variation of the feature.</text><text>Note: </text><code language=\"plain_text\">a_price = weight assigned to price (USD)\na_room  = weight assigned to number of rooms\na_lot   = weight assigned to lot size (sq.ft.)</code></co-content>"
#                   }
#                 },
#                 "options": [
#                   {
#                     "id": "0.9109180361318947",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>a_price = 1, a_room = 1, a_lot = 1</text></co-content>"
#                       }
#                     }
#                   },
#                   {
#                     "id": "0.11974743029080992",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>a_price = 1, a_room = 1, a_lot = 1e-6</text></co-content>"
#                       }
#                     }
#                   },
#                   {
#                     "id": "0.8214165539451299",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>a_price = 1e-10, a_room = 1, a_lot = 1e-6</text></co-content>"
#                       }
#                     }
#                   },
#                   {
#                     "id": "0.6784789645868041",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>a_price = 1e-5, a_room = 1, a_lot = 1e-3</text></co-content>"
#                       }
#                     }
#                   },
#                   {
#                     "id": "0.9664001374497642",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>a_price = 1e5, a_room = 1, a_lot = 1e3</text></co-content>"
#                       }
#                     }
#                   }
#                 ]
#               },
#               "detailLevel": "Full"
#             },
#             "weightedScoring": {
#               "maxScore": 1
#             },
#             "isSubmitAllowed": true
#           },
#           {
#             "id": "jeVDBjnNEeaetxLgjw7H8Q@0",
#             "question": {
#               "type": "singleNumeric"
#             },
#             "variant": {
#               "definition": {
#                 "prompt": {
#                   "typeName": "cml",
#                   "definition": {
#                     "dtdId": "assess/1",
#                     "value": "<co-content><text>\n\nConsider the following two sentences.\n</text><list bulletType=\"bullets\"><li><text>Sentence 1: The quick brown fox jumps over the lazy dog.\n</text></li><li><text>Sentence 2: A quick brown dog outpaces a quick fox.\n</text></li></list><text>\n\nCompute the Euclidean distance using word counts. Round your answer to 3 decimal places.</text><text>Note. To compute word counts, turn all words into lower case and strip all punctuation, so that \"The\" and \"the\" are counted as the same token.</text></co-content>"
#                   }
#                 }
#               },
#               "detailLevel": "Full"
#             },
#             "weightedScoring": {
#               "maxScore": 1
#             },
#             "isSubmitAllowed": true
#           },
#           {
#             "id": "-tI-EjnNEeaPCw5NUSdt1w@0",
#             "question": {
#               "type": "singleNumeric"
#             },
#             "variant": {
#               "definition": {
#                 "prompt": {
#                   "typeName": "cml",
#                   "definition": {
#                     "dtdId": "assess/1",
#                     "value": "<co-content><text>Refer back to the two sentences given in Question 2 to answer the following:</text><text>Recall that we can use cosine similarity to define a distance.  We call that distance cosine distance. </text><text>Compute the <strong>cosine distance</strong> using word counts. Round your answer to 3 decimal places.\n</text><text>Note: To compute word counts, turn all words into lower case and strip all punctuation, so that \"The\" and \"the\" are counted as the same token.</text><text>Hint. Recall that we can use cosine similarity to define a distance.  We call that distance cosine distance.</text></co-content>"
#                   }
#                 }
#               },
#               "detailLevel": "Full"
#             },
#             "weightedScoring": {
#               "maxScore": 1
#             },
#             "isSubmitAllowed": true
#           }
#         ],
#         "evaluation": null
#       }
#     }
#   ],
#   "paging": null,
#   "linked": {
#     "gradingAttempts.v1": []
#   }
# }
#
# Request payload:
# {"courseId":"-N44X0IJEeWpogr5ZO8qxQ","itemId":"YV0W4"}
#
#POST_OPENCOURSE_ONDEMAND_EXAM_SESSIONS = 'https://api.coursera.org/api/onDemandExamSessions.v1/-N44X0IJEeWpogr5ZO8qxQ~YV0W4~10!~1467462079068/actions?includes=gradingAttempts'

# Response for this request is empty. Result (session_id) should be taken
# either from Location header or from X-Coursera-Id header.
#
# Request payload:
# {"courseId":"-N44X0IJEeWpogr5ZO8qxQ","itemId":"YV0W4"}
POST_OPENCOURSE_ONDEMAND_EXAM_SESSIONS = 'https://api.coursera.org/api/onDemandExamSessions.v1'

# Sample response:
# {
#   "elements": [
#     {
#       "id": 0,
#       "result": {
#         "questions": [
#           {
#             "id": "8uUpMzm_EeaetxLgjw7H8Q@0",
#             "question": {
#               "type": "mcq"
#             },
#             "variant": {
#               "definition": {
#                 "prompt": {
#                   "typeName": "cml",
#                   "definition": {
#                     "dtdId": "assess/1",
#                     "value": "<co-content><text>\n\nSuppose you’d like to perform nearest neighbor search from the following set of houses:</text><table rows=\"5\" columns=\"4\"><tr><td><text>\n\n\n\n\n\n</text></td><td><text>\n\n\nPrice (USD)</text></td><td><text>\n\n\nNumber of rooms</text></td><td><text>\n\n\nLot size (sq. ft.)</text></td></tr><tr><td><text>\n\n\nHouse 1</text></td><td><text>\n\n\n500000</text></td><td><text>\n\n\n3</text></td><td><text>\n\n\n1840</text></td></tr><tr><td><text>\n\n\nHouse 2</text></td><td><text>\n\n\n350000</text></td><td><text>\n\n\n2</text></td><td><text>\n\n\n1600</text></td></tr><tr><td><text>House 3</text></td><td><text>\n\n600000</text></td><td><text>\n\n4</text></td><td><text>\n\n2000</text></td></tr><tr><td><text>House 4</text></td><td><text>\n400000</text></td><td><text>\n2</text></td><td><text>\n1900</text></td></tr></table><text>\n\nSince the features come in wildly different scales, you decide to use scaled Euclidean distances. Choose the set of weights a_i (as presented in the video lecture) that properly incorporates the relative amount of variation of the feature.</text><text>Note: </text><code language=\"plain_text\">a_price = weight assigned to price (USD)\na_room  = weight assigned to number of rooms\na_lot   = weight assigned to lot size (sq.ft.)</code></co-content>"
#                   }
#                 },
#                 "options": [
#                   {
#                     "id": "0.9109180361318947",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>a_price = 1, a_room = 1, a_lot = 1</text></co-content>"
#                       }
#                     }
#                   },
#                   {
#                     "id": "0.11974743029080992",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>a_price = 1, a_room = 1, a_lot = 1e-6</text></co-content>"
#                       }
#                     }
#                   },
#                   {
#                     "id": "0.8214165539451299",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>a_price = 1e-10, a_room = 1, a_lot = 1e-6</text></co-content>"
#                       }
#                     }
#                   },
#                   {
#                     "id": "0.6784789645868041",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>a_price = 1e-5, a_room = 1, a_lot = 1e-3</text></co-content>"
#                       }
#                     }
#                   },
#                   {
#                     "id": "0.9664001374497642",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>a_price = 1e5, a_room = 1, a_lot = 1e3</text></co-content>"
#                       }
#                     }
#                   }
#                 ]
#               },
#               "detailLevel": "Full"
#             },
#             "weightedScoring": {
#               "maxScore": 1
#             },
#             "isSubmitAllowed": true
#           },
#           {
#             "id": "jeVDBjnNEeaetxLgjw7H8Q@0",
#             "question": {
#               "type": "singleNumeric"
#             },
#             "variant": {
#               "definition": {
#                 "prompt": {
#                   "typeName": "cml",
#                   "definition": {
#                     "dtdId": "assess/1",
#                     "value": "<co-content><text>\n\nConsider the following two sentences.\n</text><list bulletType=\"bullets\"><li><text>Sentence 1: The quick brown fox jumps over the lazy dog.\n</text></li><li><text>Sentence 2: A quick brown dog outpaces a quick fox.\n</text></li></list><text>\n\nCompute the Euclidean distance using word counts. Round your answer to 3 decimal places.</text><text>Note. To compute word counts, turn all words into lower case and strip all punctuation, so that \"The\" and \"the\" are counted as the same token.</text></co-content>"
#                   }
#                 }
#               },
#               "detailLevel": "Full"
#             },
#             "weightedScoring": {
#               "maxScore": 1
#             },
#             "isSubmitAllowed": true
#           },
#           {
#             "id": "-tI-EjnNEeaPCw5NUSdt1w@0",
#             "question": {
#               "type": "singleNumeric"
#             },
#             "variant": {
#               "definition": {
#                 "prompt": {
#                   "typeName": "cml",
#                   "definition": {
#                     "dtdId": "assess/1",
#                     "value": "<co-content><text>Refer back to the two sentences given in Question 2 to answer the following:</text><text>Recall that we can use cosine similarity to define a distance.  We call that distance cosine distance. </text><text>Compute the <strong>cosine distance</strong> using word counts. Round your answer to 3 decimal places.\n</text><text>Note: To compute word counts, turn all words into lower case and strip all punctuation, so that \"The\" and \"the\" are counted as the same token.</text><text>Hint. Recall that we can use cosine similarity to define a distance.  We call that distance cosine distance.</text></co-content>"
#                   }
#                 }
#               },
#               "detailLevel": "Full"
#             },
#             "weightedScoring": {
#               "maxScore": 1
#             },
#             "isSubmitAllowed": true
#           },
#           {
#             "id": "LGECRDnOEeaetxLgjw7H8Q@0",
#             "question": {
#               "type": "mcq"
#             },
#             "variant": {
#               "definition": {
#                 "prompt": {
#                   "typeName": "cml",
#                   "definition": {
#                     "dtdId": "assess/1",
#                     "value": "<co-content><text>(True/False) For positive features, cosine similarity is always between 0 and 1.</text></co-content>"
#                   }
#                 },
#                 "options": [
#                   {
#                     "id": "0.838238929639803",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>True</text></co-content>"
#                       }
#                     }
#                   },
#                   {
#                     "id": "0.9654190569725087",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>False</text></co-content>"
#                       }
#                     }
#                   }
#                 ]
#               },
#               "detailLevel": "Full"
#             },
#             "weightedScoring": {
#               "maxScore": 1
#             },
#             "isSubmitAllowed": true
#           },
#           {
#             "id": "N62eSDnOEea5PAq35BZMoQ@0",
#             "question": {
#               "type": "mcq"
#             },
#             "variant": {
#               "definition": {
#                 "prompt": {
#                   "typeName": "cml",
#                   "definition": {
#                     "dtdId": "assess/1",
#                     "value": "<co-content><text>\n\nUsing the formula for TF-IDF presented in the lecture, complete the following sentence:</text><text>A word is assigned a zero TF-IDF weight when it appears in ____ documents. (N: number of documents in the corpus)</text></co-content>"
#                   }
#                 },
#                 "options": [
#                   {
#                     "id": "0.10877084920366831",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>N - 1</text></co-content>"
#                       }
#                     }
#                   },
#                   {
#                     "id": "0.29922629273211787",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>N/2</text></co-content>"
#                       }
#                     }
#                   },
#                   {
#                     "id": "0.69796593807345",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>N</text></co-content>"
#                       }
#                     }
#                   },
#                   {
#                     "id": "0.6731572688278926",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>0.1*N</text></co-content>"
#                       }
#                     }
#                   },
#                   {
#                     "id": "0.8467992755507772",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>100</text></co-content>"
#                       }
#                     }
#                   }
#                 ]
#               },
#               "detailLevel": "Full"
#             },
#             "weightedScoring": {
#               "maxScore": 1
#             },
#             "isSubmitAllowed": true
#           },
#           {
#             "id": "TuHdkjnOEeaPCw5NUSdt1w@0",
#             "question": {
#               "type": "mcq"
#             },
#             "variant": {
#               "definition": {
#                 "prompt": {
#                   "typeName": "cml",
#                   "definition": {
#                     "dtdId": "assess/1",
#                     "value": "<co-content><text>\n\nWhich of the following does <strong>not </strong>describe the word count document representation?</text></co-content>"
#                   }
#                 },
#                 "options": [
#                   {
#                     "id": "0.3821039264467949",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>Ignores the order of the words</text></co-content>"
#                       }
#                     }
#                   },
#                   {
#                     "id": "0.3470767421220087",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>Assigns a high score to a frequently occurring word</text></co-content>"
#                       }
#                     }
#                   },
#                   {
#                     "id": "0.3341840649172314",
#                     "display": {
#                       "typeName": "cml",
#                       "definition": {
#                         "dtdId": "assess/1",
#                         "value": "<co-content><text>Penalizes words that appear in every document</text></co-content>"
#                       }
#                     }
#                   }
#                 ]
#               },
#               "detailLevel": "Full"
#             },
#             "weightedScoring": {
#               "maxScore": 1
#             },
#             "isSubmitAllowed": true
#           }
#         ],
#         "evaluation": null
#       }
#     }
#   ],
#   "paging": null,
#   "linked": {
#     "gradingAttempts.v1": []
#   }
# }
#
# Request payload:
# {"name":"getState","argument":[]}
POST_OPENCOURSE_ONDEMAND_EXAM_SESSIONS_GET_STATE = 'https://api.coursera.org/api/onDemandExamSessions.v1/{session_id}/actions?includes=gradingAttempts'

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
INSTRUCTIONS_HTML_INJECTION_PRE = '''
<style>
body {
    padding: 50px 85px 50px 85px;
}

table th, table td {
    border: 1px solid #e0e0e0;
    padding: 5px 20px;
    text-align: left;
}
input {
    margin: 10px;
}
}
th {
    font-weight: bold;
}
td, th {
    display: table-cell;
    vertical-align: inherit;
}
img {
    height: auto;
    max-width: 100%;
}
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
  src="'''
INSTRUCTIONS_HTML_MATHJAX_URL = 'https://cdn.mathjax.org/mathjax/latest/MathJax.js'
INSTRUCTIONS_HTML_INJECTION_AFTER = '''?config=TeX-AMS-MML_HTMLorMML">
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

# The following url is the root url (tree) for a Coursera Course
OPENCOURSE_NOTEBOOK_DESCRIPTIONS = "https://hub.coursera-notebooks.org/hub/coursera_login?token={authId}&next=/"
OPENCOURSE_NOTEBOOK_LAUNCHES = "https://api.coursera.org/api/onDemandNotebookWorkspaceLaunches.v1/?fields=authorizationId%2CcontentPath%2CuseLegacySystem"
OPENCOURSE_NOTEBOOK_TREE = "https://hub.coursera-notebooks.org/user/{jupId}/api/contents/{path}?type=directory&_={timestamp}"
OPENCOURSE_NOTEBOOK_DOWNLOAD = "https://hub.coursera-notebooks.org/user/{jupId}/files/{path}?download=1"
