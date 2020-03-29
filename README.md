WordPress Bulk Uploader
===============================

- version number: 0.0.1
- author: rldotai

Overview
--------

A script for uploading multiple posts to WordPress, using Python and XML-RPC.

Installation
------------

To install use pip:

    $ pip install git+https://github.com/rldotai/bulk-upload-to-wordpress.git

(Note that I haven't published to PyPI because its utility is rather niche.)


Or clone the repo:

    $ git clone https://github.com/rldotai/bulk-upload-to-wordpress.git
    $ python setup.py install

Usage
-----

Installation provides two commands: `split_chapters` and `bulk_upload_wordpress`.
The first splits a complete work from AO3 into separate chapters, the second can be used to upload those chapters to a a WordPress instance.

The output of each command's `--help` gives some notion of how they work:

```shell
#
$ split_chapters --help
usage: split_chapters [-h] [--output OUTPUT] [--fragment] [--dry-run]
                      [--metadata]
                      input
positional arguments:
  input                 path to the HTML file of complete work from AO3

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        output directory to store the split posts in
  --fragment            flag to create fragment HTML files, rather than
                        standalone
  --dry-run, -n         run the script without actually creating any
                        files/directories.
  --metadata            extract and create accompanying files containing
                        metadata for each chapter.
```


```shell
$ bulk_upload_wordpress --help
usage: bulk_upload_wordpress [-h] [--username USERNAME] [--password PASSWORD]
                             [--url URL] [--use-post-metadata]
                             [--default-metadata DEFAULT_METADATA]
                             [--fix-html] [--dry-run] [--debug]
                             input [input ...

positional arguments:
  input                 HTML files to upload

optional arguments:
  -h, --help            show this help message and exit
  --username USERNAME   Username to post with
  --password PASSWORD   Password for user
  --url URL             XML-RPC URL to interface with, e.g.,
                        http://example.com/xmlrpc.php
  --use-post-metadata   Whether to look for and use JSON metadata information
                        for posts.
  --default-metadata DEFAULT_METADATA
                        default metadata for the posts to be uploaded.
  --fix-html            Flag to run HTML 'fixes' to avoid weird formatting
                        from WordPress
  --dry-run, -n         run the script without actually making posts.
  --debug               Enable debugging (using high-tech print statements.)
```

Example
-------

See the `example` directory.
