"""
This is a simple script used to update Confluence pages.
Built with Python 3.5.2.

AUTHOR: Tim West

Helpful Sources:
https://www.codeproject.com/Articles/1191742/Update-Confluence-Wiki-Page-Using-Python
https://community.atlassian.com/t5/Answers-Developer-Questions/How-to-update-a-page-with-Python-using-REST-API/qaq-p/480627
"""
import argparse
import getpass
import json
import keyring
import requests

# Constants: these allow access to Atlassian REST API
BASE_URL = "https://<YourDomain>.atlassian.net/wiki/rest/api/content"
VIEW_URL = "https://<YourDomain>.atlassian.net/wiki/rest/api/content/viewpage.action?pageId="


def get_page_ancestors(auth, pageid):
    """Get basic page info plus the ancestors property."""

    url = '{base}/{pageid}?expand=ancestors'.format(base=BASE_URL, pageid=pageid)

    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        return response.json()['ancestors']
    except requests.exceptions.RequestException as exc:
        print(exc)


def get_page_info(auth, pageid):
    """Get basic page info in JSON format."""

    url = '{base}/{pageid}'.format(base=BASE_URL, pageid=pageid)

    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        print(exc)


def write_data(auth, html, pageid, title=None):
    """Writes the html data to the page."""

    info = get_page_info(auth, pageid)
    ver = int(info['version']['number']) + 1
    ancestors = get_page_ancestors(auth, pageid)

    anc = ancestors[-1]
    del anc['_links']
    del anc['_expandable']
    del anc['extensions']

    if title is not None:
        info['title'] = title

    new_data = {
        'id' : str(pageid),
        'type' : 'page',
        'title' : info['title'],
        'version' : {'number' : ver},
        'ancestors' : [anc],
        'body'  : {
            'storage' :
            {
                'representation' : 'storage',
                'value' : str(html),
            }
        }
    }

    data = json.dumps(new_data)
    url = '{base}/{pageid}'.format(base=BASE_URL, pageid=pageid)
    response = requests.put(
        url,
        data=data,
        auth=auth,
        headers={'Content-Type' : 'application/json'}
    )

    response.raise_for_status()

    print("Wrote '%s' version %d" % (info['title'], ver))
    print("URL: %s%d" % (VIEW_URL, pageid))


def get_login(username=None):
    """ Get the password for username out of the keyring."""

    if username is None:
        username = getpass.getuser()

    password = keyring.get_password('confluence_script', username)

    if password is None:
        password = getpass.getpass()
        keyring.set_password('confluence_script', username, password)

    return (username, password)


def main():
    """Main method for the script."""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-u",
        "--user",
        default=getpass.getuser(),
        help="Specify the username to log into Confluence")

    parser.add_argument(
        "-t",
        "--title",
        default=None,
        type=str,
        help="Specify a new title")

    parser.add_argument(
        "-f",
        "--file",
        default=None,
        type=str,
        help="Write the contents of FILE to the confluence page")

    parser.add_argument(
        "pageid",
        type=int,
        help="Specify the Conflunce page id to overwrite")

    parser.add_argument(
        "html",
        type=str,
        default=None,
        nargs='?',
        help="Write the immediate html string to confluence page")

    options = parser.parse_args()
    auth = get_login(options.user)

    if options.html is not None and options.file is not None:
        raise RuntimeError(
            "Can't specify both a file and immediate html to write to page!")

    if options.html:
        html = options.html

    else:
        with open(options.file, 'r') as file_data:
            html = file_data.read()

    write_data(auth, html, options.pageid, options.title)

if __name__ == "__main__":
    main()
