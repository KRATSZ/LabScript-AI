import os


def getTravisBranch():
    # https://graysonkoonce.com/getting-the-current-branch-name-during-a-pull-request-in-travis-ci/  # noqa: E501
    if os.environ.get('TRAVIS_PULL_REQUEST') == 'false':
        return os.environ.get('TRAVIS_BRANCH')
    else:
        # don't use TRAVIS_BRANCH -- that is the PR target (eg, master)
        return os.environ.get('TRAVIS_PULL_REQUEST_BRANCH')


if __name__ == '__main__':
    print(getTravisBranch())
