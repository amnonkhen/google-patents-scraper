# google-patents-scraper
A simple scraper for the Google patents website I wrote as a freelance project. Saves each patent's HTML, images and PDF in a directory.

1. Requirements
  * Python 2.7 - https://www.python.org/download/releases/2.7/
  * pip - https://pip.pypa.io/en/latest/installing.html#install-pip
  * lxml - run pip install lxml

1. Command line parameters:
```
  -h, --help            show this help message and exit
  --start START         start patent id (default: None)
  --end END             end patent id (inclusive) (default: None)
  --output_dir OUTPUT_DIR
                        output directory (default: ./)
  --org {EP,US,WO,DE}   prefix of the organization publishing the patent
                        (default: EP)
```

  example command line:  
  `python scraper.py --start 234 --end 1872`



