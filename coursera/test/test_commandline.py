"""
Test command line module.
"""

from coursera import commandline
from coursera.test import test_workflow


def test_class_name_arg_required():
    args = {'list_courses': False, 'version': False}
    mock_args = test_workflow.MockedCommandLineArgs(**args)
    assert commandline.class_name_arg_required(mock_args)


def test_class_name_arg_not_required():
    not_required_cases = [
        {'list_courses': True, 'version': False},
        {'list_courses': False, 'version': True},
        {'list_courses': True, 'version': True},
    ]
    for args in not_required_cases:
        mock_args = test_workflow.MockedCommandLineArgs(**args)
        assert not commandline.class_name_arg_required(mock_args)
