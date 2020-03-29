__doc__ = f"""
------------------------------------------------------------------------------
A script for bulk uploading posts to WordPress.

Example:
    python {__file__} posts/*.html --url "https://my-website/xmlrpc.php" \
        --username="my_username" \
        --password="my_password" \
        --default-metadata="meta.json" \
        --use-post-metadata

------------------------------------------------------------------------------
"""
import argparse
import datetime
import json
import sys
from pathlib import Path
import bs4
from werkzeug.utils import secure_filename

from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetPosts, EditPost, NewPost


def main(args=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input", nargs="+", help="HTML files to upload")
    parser.add_argument("--username", help="Username to post with")
    parser.add_argument("--password", help="Password for user")
    parser.add_argument(
        "--url",
        help="XML-RPC URL to interface with, e.g., http://example.com/xmlrpc.php",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="run the script without actually making posts.",
    )
    parser.add_argument(
        "--use-post-metadata",
        action="store_true",
        help="Whether to look for and use JSON metadata information for posts.",
    )
    parser.add_argument(
        "--default-metadata", help="default metadata for the posts to be uploaded."
    )

    if args is None:
        args = parser.parse_args(sys.argv[1:])

    # TODO: Allow providing these from config file, or via builtin lib
    username = args.username
    password = args.password

    # Paths to files
    paths = [Path(x) for x in args.input]

    # Using default metadata
    if args.default_metadata:
        base_meta_path = Path(args.default_metadata)
        if base_meta_path.is_file():
            print(f"Loading base metadata: {base_meta_path!s}")
            meta_base = json.load(open(base_meta_path, "r"))
        else:
            raise Exception(f"{base_meta_path!s} is not a file.")

    # Connect to WordPress
    wp = Client(args.url, username, password)

    # Load the page
    for path in paths:
        print(f"Loading post: {path!s}")
        html = open(path, "r").read()

        if args.use_post_metadata:
            meta_path = path.with_suffix(".json")
            if meta_path.is_file():
                print(f"Loading metadata: {meta_path!s}")
                meta_post = json.load(open(meta_path, "r"))

                # Combine the two, prioritizing keys/values from `meta_post`
                metadata = {**meta_base, **meta_post}

        # Create post
        post = WordPressPost()

        # Set metadata attributes
        for k, v in metadata.items():
            setattr(post, k, v)

        # Set content from the html file
        # post.content = html
        post.content = ""  # DEBUG

        # Upload the post
        wp.call(NewPost(post))

        # Debugging
        # print(post.struct)


if __name__ == "__main__":
    main()
