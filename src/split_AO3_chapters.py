__doc__ = f"""
------------------------------------------------------------------------------
Split chapters of an Archive Of Our Own full HTML export by parsing the HTML.

Example:
    # Split your favorite fiction into separate HTML files stored in `./posts/`
    python {__file__} my-immortal.html --output=./posts


It can save the results as HTML fragments, but by default it extracts the HTML
for each chapter and wraps it to create valid standalone webpages.

NB:
    It's not really tested against multiple fictions, so modification may be
    necessary if your file's structure deviates from what I developed it on.
------------------------------------------------------------------------------
"""
import argparse
import json
import sys
from pathlib import Path

import bs4
from werkzeug.utils import secure_filename


def main(args=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input", help="path to the HTML file of complete work from AO3")
    parser.add_argument(
        "--output", "-o", help="output directory to store the split posts in"
    )
    parser.add_argument(
        "--fragment",
        action="store_true",
        help="flag to create fragment HTML files, rather than standalone",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="run the script without actually creating any files/directories.",
    )
    parser.add_argument(
        "--metadata",
        action="store_true",
        help="extract and create accompanying files containing metadata for each chapter.",
    )

    if args is None:
        args = parser.parse_args(sys.argv[1:])
    source = Path(args.input)
    outdir = Path(args.output)

    # Make the directory if it doesn't exist
    if not outdir.exists() and not args.dry_run:
        outdir.mkdir(parents=True)

    html = open(source, "r").read()
    soup = bs4.BeautifulSoup(html, "html.parser")

    # Also as lines -- arguably inelegant, but `sourcepos` from bs4 failed, so.
    lines = open(source, "r").readlines()

    # Chapters seem to correspond with "meta group" `divs`
    # So we capture everything between each such `div`
    group_divs = soup.find_all("div", {"class": "meta group"})
    line_posns = [el.sourceline for el in group_divs]

    # Position for the end of the final chapter has to be handled separately
    # I think this is added in automatically at the end of the work by AO3
    final_posn = soup.find("div", {"id": "afterword"}).sourceline
    line_posns.append(final_posn)

    # Build up chapters
    chapters = []
    for ix in range(len(line_posns) - 1):
        beg = line_posns[ix] - 1
        end = line_posns[ix + 1] - 1
        chapters.append(lines[beg:end])
    print(f"Found: {len(chapters)} chapters")

    # Convert to strings
    chapters = ["\n".join(c) for c in chapters]

    # Write chapters to HTML files
    for ix, chap in enumerate(chapters):
        # Parse the chapter (again) to get title information
        # We use the `lxml` parser because it produces complete (valid) pages
        cs = bs4.BeautifulSoup(chap, "lxml")
        heading = cs.find("h2", {"class": "heading"})
        title = heading.get_text(strip=True)

        # Filename and path -- secure filenames via werkzeug
        name = f"{ix+1:03d}-{title.lower():s}.html"
        name = secure_filename(name)
        dest = outdir / name
        dest = dest

        # Metadata -- potentially useful for working with the posts later
        metadata = {
            "_index": ix + 1,
            "title": title,
        }

        # Whether to create standalone HTML pages or just extract fragments
        if args.fragment:
            # As HTML fragments - TODO: maybe heading should be included?
            chapdiv = cs.find_all("div", {"class": "userstuff"})
            content = "".join(map(str, chapdiv))
        else:
            content = cs.prettify(formatter="minimal")  # as complete HTML file

        # Save chapter HTML
        if not args.dry_run:
            print(f"saving chapter to: {dest}")
            with open(dest, "w") as f:
                f.write(content)
        else:
            print(f"[DRY RUN] saving chapter to: {dest}")

        # Optionally save metadata (such as it is)
        if args.metadata:
            meta_dest = dest.with_suffix(".json")
            if not args.dry_run:
                print(f"saving metadata to: {meta_dest}")
                with open(meta_dest, "w") as f:
                    json.dump(metadata, f, indent=2)
            else:
                print(f"[DRY RUN] saving metadata to: {meta_dest}")


if __name__ == "__main__":
    main()
