from coursera.filtering import skip_format_url


def test_filter():
    test_cases = [
        (True, 'ipynb', 'http://localhost:8888/notebooks/machine-learning-specialization-private/course-4/2_kmeans-with-text-data_sklearn.ipynb#Takeaway'),
        (True, '', 'http://developer.android.com/reference/android/location/Location.html'),
        (True, '', 'http://www.apache.org/licenses/LICENSE-2.0'),
        (True, 'com', 'http://swirlstats.com'),
        (True, 'com', 'http://swirlstats.com/'),
        (True, 'com', 'mailto:user@server.com'),
        (True, 'txt*md', 'http://www.apache.org/licenses/LICENSE.txt-md'),

        (False, 'zip', 'https://s3-us-west-2.amazonaws.com/coursera-temporary/images.zip'),
        (False, 'html', 'http://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html'),
        (False, 'html', 'http://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html#subsection'),
        (False, 'asp', 'http://www.investopedia.com/terms/t/transaction.asp'),
        (False, 'cfm', 'http://papers.ssrn.com/sol3/papers.cfm?abstract_id=2235922'),
        (False, 'cfm', 'http://papers.ssrn.com/sol3/papers.cfm?abstract_id=937020.'),
        (False, 'cgi', 'http://chicagounbound.uchicago.edu/cgi/viewcontent.cgi?article=1401&context=law_and_economics'),
        (False, 'do', 'http://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri=CELEX:12008E101:EN:HTML'),
        (False, 'edu', 'https://www.facebook.com/illinois.edu'),
        (False, 'file', 'http://phx.corporate-ir.net/External.File?item=UGFyZW50SUQ9MjMzODh8Q2hpbGRJRD0tMXxUeXBlPTM=&t=1'),
        (False, 'pdf', 'http://www.gpo.gov/fdsys/pkg/FR-2011-04-14/pdf/2011-9020.pdf'),
        (False, 'pdf', 'https://d3c33hcgiwev3.cloudfront.net/_fc37f1cdf6ffbc39a2b0114bb281ddbe_IMBA-2015-4_ECON529_Esfahani_M1L3V2.pdf?Expires=1467676800&Signature=OO0ZJwbXdj9phKyVm6FA5ueCzFZzlEd15-10txezfIIui~bu18Omcnzhr0MgjoCi3TY06R0MT0NzKsAAmdJu4cQZzhqShfRUB5VsOl~xQbXzIRgqMHR15M7ro4eTX6DvTK3-kmTST6sEAnxUcdKCyQrliSoXVOkE13e5dwWlHAA_&Key-Pair-Id=APKAJLTNE6QMUY6HBC5A'),
    ]

    for expected_result, fmt, url in test_cases:
        assert expected_result == skip_format_url(fmt, url)
