# article-scraping
for summer 2017 news article scraping

## Issue records
* on python3 now
* need to deal with quotes where they go like "[not exact matches]"

* get more articles by same author?
```
def track_author(tree, author_tag):
  html_auth_tag = author_tag.replace("/text()", "")
  linkls = []

  html_ls = []
  if author_tag == 'N/A':
    return [paper_type], linkls
  authors = []
  for tag in author_tag.split("AND"):
    authors.extend(tree.xpath(tag))
    html_ls.extend(tree.xpath(html_auth_tag))
    for l in linkls:
      ls = html.fromstring(body).xpath("//a")
      url = l.get('href')

  if paper_type == 'cnn':
    authors = authors[0].replace("By ", "").replace(" and ", ", ").replace(", CNN", "").split(", ")
  return authors, linkls
```
