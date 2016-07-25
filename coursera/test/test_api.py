"""
Test APIs.
"""
import json

import pytest
from mock import patch

from coursera import api
from coursera import define

from coursera.test.utils import slurp_fixture
from coursera.utils import BeautifulSoup


@pytest.fixture
def course():
    course = api.CourseraOnDemand(
        session=None, course_id='0', course_name='test_course')
    return course


@patch('coursera.api.get_page_json')
def test_ondemand_programming_supplement_no_instructions(get_page_json, course):
    no_instructions = slurp_fixture('json/supplement-programming-no-instructions.json')
    get_page_json.return_value = json.loads(no_instructions)

    output = course.extract_links_from_programming('0')
    assert {} == output


@patch('coursera.api.get_page_json')
def test_ondemand_programming_supplement_empty_instructions(get_page_json, course):
    empty_instructions = slurp_fixture('json/supplement-programming-empty-instructions.json')
    get_page_json.return_value = json.loads(empty_instructions)
    output = course.extract_links_from_programming('0')

    # Make sure that SOME html content has been extracted, but remove
    # it immeditely because it's a hassle to properly prepare test input
    # for it. FIXME later.
    assert 'html' in output
    del output['html']

    assert {} == output


@patch('coursera.api.get_page_json')
def test_ondemand_programming_supplement_one_asset(get_page_json, course):
    one_asset_tag = slurp_fixture('json/supplement-programming-one-asset.json')
    one_asset_url = slurp_fixture('json/asset-urls-one.json')
    asset_json = json.loads(one_asset_url)
    get_page_json.side_effect = [json.loads(one_asset_tag),
                                 json.loads(one_asset_url)]

    expected_output = {'pdf': [(asset_json['elements'][0]['url'],
                               'statement-pca')]}
    output = course.extract_links_from_programming('0')

    # Make sure that SOME html content has been extracted, but remove
    # it immeditely because it's a hassle to properly prepare test input
    # for it. FIXME later.
    assert 'html' in output
    del output['html']

    assert expected_output == output


@patch('coursera.api.get_page_json')
def test_ondemand_programming_supplement_three_assets(get_page_json, course):
    three_assets_tag = slurp_fixture('json/supplement-programming-three-assets.json')
    three_assets_url = slurp_fixture('json/asset-urls-three.json')
    get_page_json.side_effect = [json.loads(three_assets_tag),
                                 json.loads(three_assets_url)]

    expected_output = json.loads(slurp_fixture('json/supplement-three-assets-output.json'))
    output = course.extract_links_from_programming('0')
    output = json.loads(json.dumps(output))

    # Make sure that SOME html content has been extracted, but remove
    # it immeditely because it's a hassle to properly prepare test input
    # for it. FIXME later.
    assert 'html' in output
    del output['html']

    assert expected_output == output


@patch('coursera.api.get_page_json')
def test_extract_links_from_lecture_assets_typename_asset(get_page_json, course):
    open_course_assets_reply = slurp_fixture('json/supplement-open-course-assets-reply.json')
    api_assets_v1_reply = slurp_fixture('json/supplement-api-assets-v1-reply.json')
    get_page_json.side_effect = [json.loads(open_course_assets_reply),
                                 json.loads(api_assets_v1_reply)]

    expected_output = json.loads(slurp_fixture('json/supplement-extract-links-from-lectures-output.json'))
    assets = ['giAxucdaEeWJTQ5WTi8YJQ']
    output = course._extract_links_from_lecture_assets(assets)
    output = json.loads(json.dumps(output))
    assert expected_output == output


@patch('coursera.api.get_page_json')
def test_extract_links_from_lecture_assets_typname_url_and_asset(get_page_json, course):
    """
    This test makes sure that _extract_links_from_lecture_assets grabs url
    links both from typename == 'asset' and == 'url'.
    """
    get_page_json.side_effect = [
        json.loads(slurp_fixture('json/supplement-open-course-assets-typename-url-reply-1.json')),
        json.loads(slurp_fixture('json/supplement-open-course-assets-typename-url-reply-2.json')),
        json.loads(slurp_fixture('json/supplement-open-course-assets-typename-url-reply-3.json')),
        json.loads(slurp_fixture('json/supplement-open-course-assets-typename-url-reply-4.json')),
        json.loads(slurp_fixture('json/supplement-open-course-assets-typename-url-reply-5.json')),
    ]

    expected_output = json.loads(slurp_fixture('json/supplement-extract-links-from-lectures-url-asset-output.json'))
    assets = ['Yry0spSKEeW8oA5fR3afVQ',
              'kMQyUZSLEeWj-hLVp2Pm8w',
              'xkAloZmJEeWjYA4jOOgP8Q']
    output = course._extract_links_from_lecture_assets(assets)
    output = json.loads(json.dumps(output))
    assert expected_output == output

@patch('coursera.api.get_page_json')
def test_list_courses(get_page_json, course):
    """
    Test course listing method.
    """
    get_page_json.side_effect = [
        json.loads(slurp_fixture('json/list-courses-input.json'))
    ]
    expected_output = json.loads(slurp_fixture('json/list-courses-output.json'))
    expected_output = expected_output['courses']
    output = course.list_courses()
    assert expected_output == output


@pytest.mark.parametrize(
    "input_filename,output_filename", [
        ('empty-input.json', 'empty-output.txt'),
        ('answer-text-replaced-with-span-input.json', 'answer-text-replaced-with-span-output.txt'),
        ('question-type-textExactMatch-input.json', 'question-type-textExactMatch-output.txt'),
        ('question-type-checkbox-input.json', 'question-type-checkbox-output.txt'),
        ('question-type-mcq-input.json', 'question-type-mcq-output.txt'),
        ('question-type-singleNumeric-input.json', 'question-type-singleNumeric-output.txt'),
        ('question-type-unknown-input.json', 'question-type-unknown-output.txt'),
        ('multiple-questions-input.json', 'multiple-questions-output.txt'),
    ]
)
def test_quiz_exam_to_markup_converter(input_filename, output_filename):
    quiz_json = json.loads(slurp_fixture('json/quiz-to-markup/%s' % input_filename))
    expected_output = slurp_fixture('json/quiz-to-markup/%s' % output_filename).strip()

    converter = api.QuizExamToMarkupConverter(session=None)
    actual_output = converter(quiz_json).strip()
    # print('>%s<' % expected_output)
    # print('>%s<' % actual_output)
    assert actual_output == expected_output


class TestMarkupToHTMLConverter:
    def _p(self, html):
        return BeautifulSoup(html).prettify()

    STYLE = None

    def setup_method(self, test_method):
        self.STYLE = self._p(define.INSTRUCTIONS_HTML_INJECTION)
        self.markup_to_html = api.MarkupToHTMLConverter(session=None)

    def test_empty(self):
        output = self.markup_to_html("")
        assert self.STYLE == output

    def test_replace_text_tag(self):
        output = self.markup_to_html("""
        <co-content>
        <text>
            Test<text>Nested</text>
        </text>
        <text>
            Test2
        </text>
        </co-content>
        """)
        assert self._p("""
        <co-content>
        <p>
            Test<p>Nested</p>
        </p>
        <p>
            Test2
        </p>
        </co-content>\n
        """) + self.STYLE == output

    def test_replace_heading(self):
        output = self.markup_to_html("""
        <co-content>
            <heading level="1">Text</heading>
            <heading level="2">Text</heading>
            <heading level="3">Text</heading>
            <heading level="4">Text</heading>
            <heading level="5">Text</heading>
            <heading >Text</heading>
        </co-content>
        """)
        assert self._p("""
        <co-content>
            <h1 level="1">Text</h1>
            <h2 level="2">Text</h2>
            <h3 level="3">Text</h3>
            <h4 level="4">Text</h4>
            <h5 level="5">Text</h5>
            <h1>Text</h1>
        </co-content>\n
        """) + self.STYLE == output

    def test_replace_code(self):
        output = self.markup_to_html("""
        <co-content>
            <code>Text</code>
            <code>Text</code>
        </co-content>
        """)
        assert self._p("""
        <co-content>
            <pre>Text</pre>
            <pre>Text</pre>
        </co-content>\n
        """) + self.STYLE == output

    def test_replace_list(self):
        output = self.markup_to_html("""
        <co-content>
            <list bullettype="numbers">Text</list>
            <list bullettype="bullets">Text</list>
        </co-content>
        """)
        assert self._p("""
        <co-content>
            <ol bullettype="numbers">Text</ol>
            <ul bullettype="bullets">Text</ul>
        </co-content>\n
        """) + self.STYLE == output


def test_quiz_converter():
    pytest.skip()
    quiz_to_markup = api.QuizExamToMarkupConverter(session=None)
    markup_to_html = api.MarkupToHTMLConverter(session=None)

    quiz_data = json.load(open('quiz.json'))['contentResponseBody']['return']
    result = markup_to_html(quiz_to_markup(quiz_data))
    # from ipdb import set_trace; set_trace(context=20)
    print('RESULT', result)
    with open('quiz.html', 'w') as file:
        file.write(result)

def test_quiz_converter_all():
    pytest.skip()
    import os

    from coursera.coursera_dl import get_session
    from coursera.cookies import login
    session = None
    session = get_session()

    quiz_to_markup = api.QuizExamToMarkupConverter(session=session)
    markup_to_html = api.MarkupToHTMLConverter(session=session)

    path = 'quiz_json'
    for filename in os.listdir(path):
    # for filename in ['all_question_types.json']:
        # if 'YV0W4' not in filename:
        #     continue
        # if 'QVHj1' not in filename:
        #     continue

        #quiz_data = json.load(open('quiz.json'))['contentResponseBody']['return']
        current = os.path.join(path, filename)
        print(current)
        quiz_data = json.load(open(current))
        result = markup_to_html(quiz_to_markup(quiz_data))
        # from ipdb import set_trace; set_trace(context=20)
        # print('RESULT', result)
        with open('quiz_html/' + filename + '.html', 'w') as f:
            f.write(result)
