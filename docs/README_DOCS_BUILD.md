How to generate documentation
--

Install    `myst_parser` and other required Sphinx extension

``` 
pip install myst-parser sphinx-rtd-theme
```


```
# in side /docs directory
make clean  # clean any existing builds
make html   # build the documentation

```

The documentation should be built in `build/html/`. You can view it by opening `build/html/index.html` in your browser:

```
# For Linux
xdg-open build/html/index.html

# For macOS
# open build/html/index.html

# For Windows
# start build/html/index.html

```