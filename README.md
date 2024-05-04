# LeSSI

Logical, Structural, and Semantic Interpretation

Crawling Web News and storing them in JSON Format

This project crawls the news' RSS Feed and optionally retrieves articles being stored in the Web Archive. This then extracts the full-text of an article, and it dumps it in a JSON semistructured file. All the articles are then associated to a timestamp. Articles that were not successfully parsed are dumped raw as HTML in a ```extra``` folder. Have a look at the shell script for an idea on how to make things work.
