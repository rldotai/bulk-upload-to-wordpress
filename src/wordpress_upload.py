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
import copy
import datetime
import json
import sys
import textwrap
from pathlib import Path
import bs4
from werkzeug.utils import secure_filename

from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetPosts, EditPost, NewPost


def fix_html(post) -> str:
    """Fix up HTML so that WordPress doesn't mangle it"""
    # Try to handle different possible types
    if isinstance(post, WordPressPost):
        ret = copy.copy(post.content)
    elif isinstance(post, str):
        ret = post

    # WordPress treats newlines as semantic content; undesirable in some cases
    # Remove newlines before/after <span> elements
    ret = ret.replace("</span>\n<em>\n<span", "</span><em><span")
    ret = ret.replace("</span>\n</em>\n<span>", "</span></em><span>")

    ret = ret.replace("<em>\n<span", "<em><span")
    ret = ret.replace("</span>\n</em>", "</span></em>")

    # Remove newlines before/after bold elements
    ret = ret.replace("<b>\n<em>", "<b><em>")
    ret = ret.replace("</em>\n</b>", "</em></b>")
    return ret


def struct2string(post) -> str:
    """An attempt to pretty-print XML-RPC struct objects."""
    ret = []
    for k, v in post.struct.items():
        if k != "post_content":
            ret.append(f"{k:20s} : {v!s}, {type(v)!s}")
        elif k == "post_content":
            content = "\n".join([v[:100], "\n[...]\n", v[-100:]])
            content = textwrap.fill(content, width=60, replace_whitespace=False)
            content = textwrap.indent(content, "    ")
            ret.append(f"{k:20s}: ")
            ret.append(content)

    return "\n".join(ret)


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
        "--use-post-metadata",
        action="store_true",
        help="Whether to look for and use JSON metadata information for posts.",
    )
    parser.add_argument(
        "--default-metadata",
        type=Path,
        help="default metadata for the posts to be uploaded.",
    )
    parser.add_argument(
        "--fix-html",
        action="store_true",
        help="Flag to run HTML 'fixes' to avoid weird formatting from WordPress",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="run the script without actually making posts.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debugging (using high-tech print statements.)",
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
    else:
        meta_base = {}

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
        else:
            meta_post = {}

        # Combine metadata for post, prioritizing keys/values from `meta_post`
        metadata = {**meta_base, **meta_post}

        # Create post
        post = WordPressPost()

        # Extract info from metadata (if available), use it to fill in post fields
        index = metadata.get("_index", "")
        slug_prefix = metadata.get("_slug_prefix", "")
        title_prefix = metadata.get("_title_prefix", "")
        title = metadata.get("title", "")

        # Sanitize the slug (since it will be part of the URL)
        title_slug = secure_filename(title.lower().replace(" ", "-"))

        # Generate slugs and title
        post_slug = f"{slug_prefix}-{index:s}-{title_slug:s}"
        post_title = f"{title_prefix} {index:s}: {title:s}"

        # Set metadata attributes
        for k, v in metadata.items():
            # Filter keys that aren't used for XML-RPC.
            if not k.startswith("_"):
                setattr(post, k, v)

        # Set content from the html file
        html = fix_html(html)
        post.content = html

        # Upload the post
        if not args.dry_run:
            print(f"Uploading post for {path!s}...")
            res = wp.call(NewPost(post))
        else:
            print(f"[DRY RUN] Uploading post for {path!s}...")

        # Debugging
        if args.debug:
            struct_rep = struct2string(post)
            struct_rep = textwrap.indent(struct_rep, "    ")
            print(struct_rep)


if __name__ == "__main__":
    main()
