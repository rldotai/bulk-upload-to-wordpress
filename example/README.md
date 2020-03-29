# Preliminaries

Install the package (see the README in the root directory), because it's the fastest way to get the dependencies for the script working.
Also, it makes the command line functions we're going to use globally available, which is a minor convenience (otherwise you have to reference the relevant file like `python ../src/some_script.py [...args,]`).



# Creating Posts to Upload

After writing a beloved web fiction, it is well-known that the next immediate career move involves collecting donations for nebulous research on AI risk.
But in order to promote one's newly established foundation, it helps to have a more prestigious URL than a writing aggregator such as AO3; thus it becomes necessary to first download the work from such a site, before uploading it to an address more befitting.

Here we use a script that parses the downloadable full copy of a work from Archive of Our Own, splits it into separate chapters (with some metadata), and saves those files in `./posts`.

```bash
# Assuming you have the package installed
split_chapters my-immortal.html --output=./posts --metadata

# If you want to use the script directly, although you need the dependencies
../src/split_AO3_chapters.py my-immortal.html --output=./posts --metadata

# If you just want to see what would happen w/o creating directories or
# writing files, use the `--dry-run` switch
split_chapters my-immortal.html --output=./posts --metadata --dry-run
```

By default each post thus created is a standalone HTML document.
Note that you can also use `--fragment` as a command line switch to get just the HTML fragments containing each chapter.
This might be desirable if you have lots of endnotes or want to strip out everything _but_ the actual content (as of this writing this also strips out chapter headings).

(If you don't want to write metadata, omit the `--metadata` switch, although this might make the uploading part more difficult.)

---

So assuming the script worked, the results should yield a directory like
```
posts
├── 001-on-the-origin-of-the-ponies.html
├── 001-on-the-origin-of-the-ponies.json
├── 002-snape-kanye-slashfic.html
├── 002-snape-kanye-slashfic.json
[...]
├── 420-the-lay-of-lord-musk.html
├── 420-the-lay-of-lord-musk.json
├── 421-the-end.html
└── 421-the-end.json
```
...although the titles will change depending on the work in question.
The `.json` files contain metadata for each chapter, which is at present just its index and title.


# Uploading Posts

I have written a script that _should_ work out of the box, but will likely require modifications to get it working correctly, particularly if the any of the underlying APIs change.
*HOWEVER*, since the end result of this process will be a large number of posts made to your site, **please read to the end of this section instead of just copy-pasting the commands**.

---

Assuming everything will work correctly, we then run the `wordpress_upload.py` script, which if the package was installed, is given by `bulk_upload_wordpress`, or you can find the file in `src/wordpress_upload.py`.

```bash
# Print help message
bulk_upload_wordpress --help

# Upload w/ no metadata (so no titles, dates, etc. filled in) -- you probably don't want to do this
bulk_upload_wordpress ./posts/*.html --url "https://my-website/xmlrpc.php" --username="my_username" --password="my_password"
```

You need to specify the username, password, and url, otherwise this will obviously not work.
If your username/password doesn't have upload priviledges, then there'll probably be an authentication error somewhere down the line.

## Metadata

To avoid garbage uploads, or having to manually change things after the upload, we should specify some things about our posts.

Some information is available on a per-post basis, things like the post title, or its chapter index.
If you generated the posts using the `split_chapters` command, then these metadata files should be in the `./posts` directory, named like the HTML files but with a `.json` suffix.
This per-post metadata should then be found by the script.

Some aspects of each post are constant (e.g., author, post_status, etc), so we can store them in a single file.
Here, that's `defaults.json`, which I have filled out it enough detail to give you an idea of what it ought to look like.

**You should customize this depending on your site!**

In particular, things like `custom_fields`, and `terms_names`, since these set information about the template/layout and categories/post tags, although you can probably set these things as a bulk action in the WP management console, so perhaps it's not essential (and getting this information in the proper form is a little tricky).

## Fix HTML?

WordPress seems to apply additional markup to the uploaded HTML; in particular it inserts line breaks for non-semantic newlines (e.g. those separating `<span>`, `<em>`, and `<b>` tags).
Simply removing those newlines in the HTML before uploading seems to solve the problem; there's a function that will do this if you use the `--fix-html` flag.


## Actually Uploading Posts

So what we actually run would look like:

```bash
# An example using metadata, from both defaults and per-post
bulk_upload_wordpress ./posts/*.html \
--url "https://the-singularity-is-nigh.wordpress.com/xmlrpc.php" \
--username "ray" \
--default-metadata="./defaults.json"
--password "bostromisahack" \
--use-post-metadata \
--fix-html
```

You can also add in the and `--debug` flag to get a better idea of how the posts have been constructed, and `--dry-run` to run the script without actually uploading anything.

## Regarding Metadata


For the Python XML-RPC library, posts have a schema of the following form:
```
{
    'id': 'post_id',
    'user': 'post_author',
    'date': <wordpress_xmlrpc.fieldmaps.DateTimeFieldMap>,
    'date_modified': <wordpress_xmlrpc.fieldmaps.DateTimeFieldMap>,
    'slug': 'post_name',
    'post_status': 'post_status',
    'title': <wordpress_xmlrpc.fieldmaps.FieldMap>,
    'content': 'post_content',
    'excerpt': 'post_excerpt',
    'link': 'link',
    'comment_status': 'comment_status',
    'ping_status': 'ping_status',
    'terms': <wordpress_xmlrpc.fieldmaps.TermsListFieldMap>,
    'terms_names': 'terms_names',
    'custom_fields': 'custom_fields',
    'enclosure': 'enclosure',
    'password': 'post_password',
    'post_format': 'post_format',
    'thumbnail': 'post_thumbnail',
    'sticky': 'sticky',
    'post_type': <wordpress_xmlrpc.fieldmaps.FieldMap>,
    'parent_id': 'post_parent',
    'menu_order': <wordpress_xmlrpc.fieldmaps.IntegerFieldMap>,
    'guid': 'guid',
    'mime_type': 'post_mime_type'
}
```
...which seems rather laborious to setup by hand.

Fortunately, most of these can be left blank, and presumably `python-xml-rpc` chooses defaults (or WordPress does).
If you want to specify them, I would suggest using a default template which can be overwritten on a per-post basis.
So you would fill in things like "user" or something once in some JSON file and then have another JSON file for each post which could fill in "title" what have you.

I am not super certain about the type conversion-- some example code I've read seems to indicate that for keys like `terms_names`, an acceptable value is `['test', 'post']`, which is presumably then converted into the proper XML by `python-xml-rpc` when it's actually communicating with WordPress.


# WordPress XML-RPC API Notes


Compare the Python XML-RPC library's definition with the WordPress docs:

```
# https://codex.wordpress.org/XML-RPC_WordPress_API/Posts

# getPost
struct: Note that the exact fields returned depends on the fields parameter.
    string post_id
    string post_title1
    datetime post_date1
    datetime post_date_gmt1
    datetime post_modified1
    datetime post_modified_gmt1
    string post_status1
    string post_type1
    string post_format1
    string post_name1
    string post_author1 author id
    string post_password1
    string post_excerpt1
    string post_content1
    string post_parent1
    string post_mime_type1
    string link1
    string guid1
    int menu_order1
    string comment_status1
    string ping_status1
    bool sticky1
    struct post_thumbnail1: See wp.getMediaItem.
    array terms
        struct: See wp.getTerm
    array custom_fields
        struct
        string id
        string key
        string value
    struct enclosure
        string url
        int length
        string type

# newPost
int blog_id
string username
string password
struct content
    string post_type
    string post_status
    string post_title
    int post_author
    string post_excerpt
    string post_content
    datetime post_date_gmt | post_date
    string post_format
    string post_name: Encoded URL (slug)
    string post_password
    string comment_status
    string ping_status
    int sticky
    int post_thumbnail
    int post_parent
    array custom_fields
    struct
    string key
    string value
struct terms: Taxonomy names as keys, array of term IDs as values.
struct terms_names: Taxonomy names as keys, array of term names as values.
struct enclosure
    string url
    int length
    string type
any other fields support
```

References:

    - https://codex.wordpress.org/XML-RPC_WordPress_API/Posts
    - https://developer.wordpress.org/reference/functions/wp_insert_post/
