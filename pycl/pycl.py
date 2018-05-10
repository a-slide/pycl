# -*- coding: utf-8 -*-

# Strandard library imports
import os
import gzip
import shutil
import sys
import gzip
import warnings
import time
import random
from collections import OrderedDict
from subprocess import Popen, PIPE
import bisect
import itertools

##~~~~~~~ JUPYTER NOTEBOOK SPECIFIC TOOLS ~~~~~~~#

def jhelp(function, full=False, **kwargs):
    """
    Print a nice looking help string based on the name of a declared function. By default print the function
    definition and description
    * function
        Name of a declared function or class method
    * full
        If True, the help string will included a description of all arguments
    """
    # For some reason signature is not aways importable. In these cases the build-in help in invoqued
    try:
        from IPython.core.display import display, HTML, Markdown
        from inspect import signature, isfunction, ismethod
    except (NameError, ImportError) as E:
        warnings.warn ("jupyter notebook is required to use this function. Please verify your dependencies")
        help(function)
        return

    if isfunction(function) or ismethod(function):
        name = function.__name__.strip()
        sig = str(signature(function)).strip()
        display(HTML ("<b>{}</b> {}".format(name, sig)))

        if function.__doc__:
            for line in function.__doc__.split("\n"):
                line = line.strip()
                if not full and line.startswith("*"):
                    break
                display(Markdown(line.strip()))
    else:
        jprint("{} is not a function".format(function))

def stdout_print (*args):
    """
    Emulate print but uses sys stdout instead. It could sometimes be useful in specific situations where print
    is in is not behaving optimaly (like with tqdm for example)
    """
    s =  " ".join([str(i) for i in args])
    sys.stdout.write(s)
    sys.stdout.flush()

def jprint(*args, **kwargs):
    """
    FOR JUPYTER NOTEBOOK ONLY
    Format a string in HTML and print the output. Equivalent of print, but highly customizable. Many options can be
    passed to the function.
    * *args
        One or several objects that can be cast in str
    * **kwargs
        Formatting options to tweak the html rendering
        Boolean options : bold, italic, highlight, underlined, striked, subscripted, superscripted
        String oprions: font, color, size, align, background_color, line_height
    """
    # Function specific third party import
    try:
        from IPython.core.display import display, HTML
    except (NameError, ImportError) as E:
        warnings.warn ("jupyter notebook is required to use this function. Please verify your dependencies")
        print(args)
        return

    # Join the different elements together and cast in string
    s =  " ".join([str(i) for i in args])

    # Replace new lines and tab by their html equivalent
    s = s.replace("\n", "<br>").replace("\t", "&emsp;")

    # For boolean options
    if "bold" in kwargs and kwargs["bold"]: s = "<b>{}</b>".format(s)
    if "italic" in kwargs and kwargs["italic"]: s = "<i>{}</i>".format(s)
    if "highlight" in kwargs and kwargs["highlight"]: s = "<mark>{}</mark>".format(s)
    if "underlined" in kwargs and kwargs["underlined"]: s = "<ins>{}</ins>".format(s)
    if "striked" in kwargs and kwargs["striked"]: s = "<del>{}</del>".format(s)
    if "subscripted" in kwargs and kwargs["subscripted"]: s = "<sub>{}</sub>".format(s)
    if "superscripted" in kwargs and kwargs["superscripted"]: s = "<sup>{}</sup>".format(s)

    # for style options
    style=""
    if "font" in kwargs and kwargs["font"]: style+= "font-family:{};".format(kwargs["font"])
    if "color" in kwargs and kwargs["color"]: style+= "color:{};".format(kwargs["color"])
    if "size" in kwargs and kwargs["size"]: style+= "font-size:{}%;".format(kwargs["size"])
    if "align" in kwargs and kwargs["align"]: style+= "text-align:{};".format(kwargs["align"])
    if "background_color" in kwargs and kwargs["background_color"]: style+= "background-color:{};".format(kwargs["background_color"])
    if "line_height" in kwargs and kwargs["line_height"]:
        line_height = kwargs["line_height"]
    else:
        line_height=20
    style+= "line-height:{}px;".format(line_height)

    # Format final string
    if style: s = "<p style=\"{}\">{}</p>".format(style,s)
    else: s = "<p>{}</p>".format(s)

    display(HTML(s))

def toogle_code(**kwargs):
    """
    FOR JUPYTER NOTEBOOK ONLY
    Hide code with a clickable link in a j
    upyter notebook
    """
    # Function specific third party import
    try:
        from IPython.core.display import display, HTML
    except (NameError, ImportError) as E:
        warnings.warn ("jupyter notebook is required to use this function. Please verify your dependencies")
        return

    display(HTML(
    '''<script>
    code_show=true;
    function code_toggle() {
     if (code_show){
     $('div.input').hide();
     } else {
     $('div.input').show();
     }
     code_show = !code_show
    }
    $( document ).ready(code_toggle);
    </script>
    <b><a href="javascript:code_toggle()">Toggle on/off the raw code</a></b>''')
    )

def larger_display (percent=100, **kwargs):
    """
    FOR JUPYTER NOTEBOOK ONLY
    Resize the area of the screen containing the notebook according to a given percentage of the available width
    *  percent percentage of the width of the screen to use [DEFAULT:100]
    """
    # Function specific third party import
    try:
        from IPython.core.display import display, HTML
    except (NameError, ImportError) as E:
        warnings.warn ("jupyter notebook is required to use this function. Please verify your dependencies")
        return

    # resizing
    display(HTML("<style>.container {{ width:{0}% !important; }}</style>".format(percent)))

def hide_traceback ():
    """
    FOR JUPYTER NOTEBOOK ONLY
    Remove the traceback of exception and return only the Exception message and type
    """
    ipython = get_ipython()
    ipython.showtraceback = _hide_traceback

def _hide_traceback (
    exc_tuple=None,
    filename=None,
    tb_offset=None,
    exception_only=False,
    running_compiled_code=False):
    """
    Private helper function for hide_traceback
    """
    ipython = get_ipython()
    etype, value, tb = sys.exc_info()
    return ipython._showtraceback(
        etype,
        value,
        ipython.InteractiveTB.get_exception_only (etype, value))

#~~~~~~~ PREDICATES ~~~~~~~#

def is_readable_file (fp, raise_exception=True, **kwargs):
    """
    Verify the readability of a file or list of file
    """
    if not os.access(fp, os.R_OK):
        if raise_exception:
            raise IOError ("{} is not a valid file".format(fp))
        else:
            return False
    else:
        return True

def is_gziped (fp, **kwargs):
    """
    Return True if the file is Gziped else False
    """
    return fp[-2:].lower() == "gz"

def has_extension (fp, ext, pos=-1, raise_exception=False, **kwargs):
    """
    Test presence of extension in a file path
    * ext
        Single extension name or list of extension names  without dot. Example ["gz, "fa"]
    * pos
        Postition of the extension in the file path. -1 for the last, -2 for the penultimate and so on [DEFAULT -1 = Last position]
    """
    # Cast in list
    if type(ext) == str:
        ext = [ext]
    # Test ext presence
    if not fp.split(".")[pos].lower() in ext:
        if raise_exception:
            raise ValueError ("Invalid extension for file {}. Valid extensions: {}".format(fp, "/".join(ext)))
        else:
            return False
    else:
        return True

#~~~~~~~ PATH MANIPULATION ~~~~~~~#

def file_basename (fp, **kwargs):
    """
    Return the basename of a file without folder location and extension
    """
    return fp.rpartition('/')[2].partition('.')[0]

def extensions (fp, comp_ext_list=["gz", "tgz", "zip", "xz", "bz2"], **kwargs):
    """
    Return The extension of a file in lower-case. If archived file ("gz", "tgz", "zip", "xz", "bz2")
    the method will output the base extension + the archive extension as a string
    """
    split_name = fp.split("/")[-1].split(".")
    # No extension ?
    if len (split_name) == 1:
        return ""
    # Manage compressed files
    elif len (split_name) > 2 and split_name[-1].lower() in comp_ext_list:
        return ".{}.{}".format(split_name[-2], split_name[-1]).lower()
    # Normal situation = return the last element of the list
    else:
        return ".{}".format(split_name[-1]).lower()

def extensions_list (fp, comp_ext_list=["gz", "tgz", "zip", "xz", "bz2"], **kwargs):
    """
    Return The extension of a file in lower-case. If archived file ("gz", "tgz", "zip", "xz", "bz2")
    the method will output the base extension + the archive extension as a list
    """
    split_name = fp.split("/")[-1].split(".")
    # No extension ?
    if len (split_name) == 1:
        return []
    # Manage compressed files
    elif len (split_name) > 2 and split_name[-1].lower() in comp_ext_list:
        return [split_name[-2].lower(), split_name[-1].lower()]
    # Normal situation = return the last element of the list
    else:
        return [split_name[-1].lower()]

def file_name (fp, **kwargs):
    """
    Return The complete name of a file with the extension but without folder location
    """
    return fp.rpartition("/")[2]

def dir_name (fp, **kwargs):
    """
    Return the name of the directory where the file is located
    """
    return fp.rpartition("/")[0].rpartition("/")[2]

def dir_path (fp, **kwargs):
    """
    Return the directory path of a file
    """
    return fp.rpartition("/")[0]

##~~~~~~~ STRING FORMATTING ~~~~~~~#

def supersplit (string, separator="", **kwargs):
    """
    like split but can take a list of separators instead of a simple separator
    """
    if not separator:
        return string.split()

    if type(separator) == str:
        return string.split(separator)

    for sep in separator:
        string = string.replace(sep, "#")
    return string.split("#")

def rm_blank (name, replace="", **kwargs):
    """ Replace blank spaces in a name by a given character (default = remove)
    Blanks at extremities are always removed and nor replaced """
    return replace.join(name.split())

#~~~~~~~ FILE MANIPULATION ~~~~~~~#

def concatenate (src_list, dest, **kwargs):
    """
    Concatenate a list of scr files in a single output file. Handle gziped files (mixed input and output)
    """
    if is_gziped (dest):
        open_fun_dest, open_mode_dest = gzip.open, "wt"
    else:
        open_fun_dest, open_mode_dest = open, "w"
    with open_fun_dest (dest, open_mode_dest) as fh_dest:
        for src in src_list:
            if is_gziped (src):
                open_fun_src, open_mode_src = gzip.open, "rt"
            else:
                open_fun_src, open_mode_src = open, "r"
            with open_fun_src (src, open_mode_src) as fh_src:
                shutil.copyfileobj (fh_src, fh_dest)

def copyFile(src, dest, **kwargs):
    """
    Copy a single file to a destination file or folder (with error handling/reporting)
    * src
        Source file path
    * dest
        Path of the folder where to copy the source file
    """
    try:
        shutil.copy(src, dest)
    # eg. src and dest are the same file
    except shutil.Error as E:
        print('Error: %s' % E)
    # eg. source or destination doesn't exist
    except IOError as E:
        print('Error: %s' % E.strerror)

def gzip_file (fpin, fpout=None, **kwargs):
    """
    gzip a file
    * fpin
        Path of the input uncompressed file
    * fpout
        Path of the output compressed file (facultative)
    """
    # Generate a automatic name if none is given
    if not fpout:
        fpout = fpin +".gz"

    # Try to initialize handle for
    try:
        in_handle = open(fpin, "rb")
        out_handle = gzip.open(fpout, "wb")
        # Write input file in output file
        print ("Compressing {}".format(fpin))
        out_handle.write (in_handle.read())
        # Close both files
        in_handle.close()
        out_handle.close()
        return os.path.abspath(fpout)

    except IOError as E:
        print(E)
        if os.path.isfile (fpout):
            try:
                os.remove (fpout)
            except OSError:
                print ("Can't remove {}".format(fpout))

def gunzip_file (fpin, fpout=None, **kwargs):
    """
    ungzip a file
    * fpin
        Path of the input compressed file
    * fpout
        Path of the output uncompressed file (facultative)
    """
    # Generate a automatic name without .gz extension if none is given
    if not fpout:
        fpout = fpin[0:-3]

    try:
        # Try to initialize handle for
        in_handle = gzip.GzipFile(fpin, 'rb')
        out_handle = open(fpout, "wb")
        # Write input file in output file
        print ("Uncompressing {}".format(fpin))
        out_handle.write (in_handle.read())
        # Close both files
        out_handle.close()
        in_handle.close()
        return os.path.abspath(fpout)

    except IOError as E:
        print(E)
        if os.path.isfile (fpout):
            try:
                os.remove (fpout)
            except OSError:
                print ("Can't remove {}".format(fpout))

#~~~~~~~ FILE INFORMATION/PARSING ~~~~~~~#

def linerange (fp, range_list=[], line_numbering=True, max_char_line=150, **kwargs):
    """
    Print a range of lines in a file according to a list of start end lists. Handle gziped files
    * fp
        Path to the file to be parsed
    * range_list
        list of start, end coordinates lists or tuples
    * line_numbering
        If True the number of the line will be indicated in front of the line
    * max_char_line
        Maximal number of character to print per line
    """
    if not range_list:
        n_line = fastcount(fp)
        range_list=[[0,2],[n_line-3, n_line-1]]

    if is_gziped(fp):
        open_fun = gzip.open
        open_mode =  "rt"
    else:
        open_fun = open
        open_mode =  "r"

    with open_fun(fp, open_mode) as f:
        previous_line_empty = False
        for n, line in enumerate(f):
            line_print = False
            for start, end in range_list:
                if start <= n <= end:
                    if line_numbering:
                        l = "{}\t{}".format(n, line.strip())
                    else:
                        l = line.strip()

                    if len(l) > max_char_line:
                        jprint (l[0:max_char_line]+"...", line_height=10)
                    else:
                        jprint (l, line_height=10)

                    line_print = True
                    previous_line_empty = False
                    break

            if not line_print:
                if not previous_line_empty:
                    jprint("...", line_height=10)
                    previous_line_empty = True

def cat (fp, max_lines=100, line_numbering=False, max_char_line=150, **kwargs):
    """
    Emulate linux cat cmd but with line cap protection. Handle gziped files
    * fp
        Path to the file to be parsed
    * max_lines
        Maximal number of lines to print
    * line_numbering
        If True the number of the line will be indicated in front of the line
    * max_char_line
        Maximal number of character to print per line
    """
    n_line = fastcount(fp)
    if n_line <= max_lines:
        range_list = [[0, n_line-1]]
    else:
        range_list=[[0, max_lines/2-1],[n_line-max_lines/2, n_line]]
    linerange (fp=fp, range_list=range_list, line_numbering=line_numbering, max_char_line=max_char_line)

def tail (fp, n=10, line_numbering=False, max_char_line=150, **kwargs):
    """
    Emulate linux tail cmd. Handle gziped files
    * fp
        Path to the file to be parsed
    * n
        Number of lines to print starting from the end of the file
    * line_numbering
        If True the number of the line will be indicated in front of the line
    * max_char_line
        Maximal number of character to print per line
    """
    n_line = fastcount(fp)
    if n_line <= n:
        range_list = [[0, n_line]]
        jprint ("Only {} lines in the file".format(n_line))
    else:
        range_list=[[n_line-n+1, n_line]]
    linerange (fp=fp, range_list=range_list, line_numbering=line_numbering, max_char_line=max_char_line)

def head (fp, n=10, line_numbering=False, ignore_comment_line=False, comment_char="#", max_char_line=150, **kwargs):
    """
    Emulate linux head cmd. Handle gziped files
    * fp
        Path to the file to be parsed
    * n
        Number of lines to print starting from the begining of the file (Default 10)
    * line_numbering
        If True the number of the line will be indicated in front of the line (Default False)
    * ignore_comment_line
        Skip initial lines starting with a specific character (Default False)
    * comment_char
        Character or string for ignore_comment_line argument (Default "#")
    * max_char_line
        Maximal number of character to print per line (Default 150)
    """
    if is_gziped(fp):
        open_fun = gzip.open
        open_mode =  "rt"
    else:
        open_fun = open
        open_mode =  "r"

    with open_fun(fp, open_mode) as fh:

        line_num = 0
        while (line_num < n):
            try:
                l= next(fh).strip()
                if ignore_comment_line and l.startswith(comment_char):
                    continue
                if line_numbering:
                    l = "{}\t{}".format(line_num, l)
                if len(l) > max_char_line:
                    jprint (l[0:max_char_line]+"...", line_height=10)
                else:
                    jprint (l, line_height=10)
                line_num+=1

            except StopIteration:
                jprint ("Only {} lines in the file".format(line_num))
                break

def linesample (fp, n_lines=100, line_numbering=True, max_char_line=150, **kwargs):
    """
    Randomly sample lines in a file and print them. Handle gziped files
    * fp
        Path to the file to be parsed
    * n_lines
        Number of lines to sample in the file
    * line_numbering
        If True the number of the line will be indicated in front of the line
    * max_char_line
        Maximal number of character to print per line
    """
    n_lines_origin = fastcount(fp)

    # Take into account the situation in which there are less lines in the file than requested.
    if n_lines >= n_lines_origin:
        if verbose:
            print("Not enough lines in source file. Writing all reads in the output file")
        index_list = list(range(0, n_lines_origin-1))
    else:
        index_list = sorted(random.sample(range(0, n_lines_origin-1), n_lines))

    # Sample lines in input file according to the list of random line numbers
    if is_gziped(fp):
        open_fun = gzip.open
        open_mode =  "rt"
    else:
        open_fun = open
        open_mode =  "r"

    with open_fun(fp, open_mode) as fh:
        j = 0
        for i, l in enumerate(fh):
            if j >= n_lines:
                break
            if i == index_list[j]:
                j+=1
                l = l.strip()
                if len(l) > max_char_line:
                        l = l[0:max_char_line]+"..."
                if line_numbering:
                    l = "{}\t{}".format(i, l)
                jprint (l, line_height=10)

def count_uniq (fp, colnum, select_values=None, drop_values=None, skip_comment="#", sep="\t", **kwargs):
    """
    Count unique occurences in a specific column of a tabulated file
    * fp
        Path to the file to be parsed (gzipped or not)
    * colnum
        Index number of the column to summarize
    * select_values
        Select specific lines in the file based on a dictionary containing column index(es) and valu(es) or list
        of values to select. Exemple {2:["exon", "transcript"], 4:"lincRNA"}. DEFAULT=None
    * drop_values
        Same think that select_value but will drop the lines instead. DEFAULT=None
    * skip_comment
        Drop any comment lines starting with this character. DEFAULT="#"
    * sep
        Character or list of characters to use in order to split the lines. Exemple ["\t",";"]. DEFAULT="\t"
    """

    # Function specific third party import
    try:
        import pandas as pd
    except (NameError, ImportError) as E:
        print (E)
        print ("pandas is required to use this function. Please verify your dependencies")
        sys.exit()

    # Transform separator in regular expression if needed
    if type (sep) == list:
        sep = "[{}]".format("".join(sep))
        engine='python'
    else:
        engine='c'

    df = pd.read_csv(fp, sep=sep, index_col=False, header=None, comment=skip_comment, engine=engine)

    if select_values:
        for i, j in select_values.items():
            if type(j) == str:
                df = df[(df[i] == j)]
            if type(j) == list:
                df = df[(df[i].isin(j))]

    if drop_values:
        for i, j in drop_values.items():
            if type(j) == str:
                df = df[(df[i] != j)]
            if type(j) == list:
                df = df[(~df[i].isin(j))]

    return df.groupby(colnum).size().sort_values(ascending=False)

def colsum (fp,
    colrange=None,
    separator="",
    header=False,
    ignore_hashtag_line=False,
    max_items=10,
    ret_type="md",
    **kwargs):
    """
    Create a summary of selected columns of a file
    * fp
        Path to the file to be parsed
    * colrange
        A list of column index to parse
    * separator
        A character or a list of characters to split the lines
    * ignore_hashtag_line
        skip line starting with a # symbol
    * max_items
        maximum item per line
    * ret_type
        Possible return types:
        md = markdown formatted table,
        dict = raw parsing dict,
        report = Indented_text_report
    """

    res_dict = OrderedDict()

    with open(fp, "r") as f:
        # Manage the first line
        first_line = False
        header_found = False
        while not first_line:

            line = next(f)

            if ignore_hashtag_line and line[0] == "#":
                continue

            # Split the first line
            ls = supersplit(line, separator)

            if header and not header_found:
                header_dict = {}
                for colnum, val in enumerate(ls):
                    header_dict[colnum]= val
                header_found = True
                #print("Header found")
                continue

            # Get the number of col if not given and handle the first line
            if not colrange:
                colrange = [i for i in range(len(ls))]
                #print("Found {} colums".format(len(ls)))

            # Manage the first valid line
            #print("First line found")
            for colnum in colrange:
                res_dict[colnum] = OrderedDict()
                val = ls[colnum].strip()
                res_dict[colnum][val]=1
            first_line = True

        # Continue to read and parse the lines
        for line in f:
            ls = supersplit(line, separator)
            for colnum in colrange:
                val = ls[colnum].strip()
                if val not in res_dict[colnum]:
                    res_dict[colnum][val] = 0
                res_dict[colnum][val]+=1

    # Return directly the whole dict
    if ret_type == "dict":
        return res_dict

    # Return an indented text report
    if ret_type == "report":
        return dict_to_report(res_dict, tab="\t", sep="\t", sort_dict=True, max_items=max_items)

    # Create a Markdown table output per colums
    elif ret_type == "md":
        buffer=""
        for colnum, col_dict in res_dict.items():
            if header:
                buffer+= dict_to_md(col_dict, header_dict[colnum], "Count", transpose=True, sort_by_val=True, max_items=max_items)
            else:
                buffer+= dict_to_md(col_dict, colnum, "Count", transpose=True, sort_by_val=True, max_items=max_items)
            buffer+='\n'
        return buffer
    else:
        print ("Invalid return type")

def fastcount(fp, **kwargs):
    """
    Efficient way to count the number of lines in a file. Handle gziped files
    """
    if is_gziped(fp):
        open_fun = gzip.open
        open_mode =  "rt"
    else:
        open_fun = open
        open_mode =  "r"

    with open_fun(fp, open_mode) as fh:
        lines = 0
        buf_size = 1024 * 1024
        read_f = fh.read # loop optimization

        buf = read_f(buf_size)
        while buf:
            lines += buf.count('\n')
            buf = read_f(buf_size)

    return lines

def simplecount(fp, ignore_hashtag_line=False, **kwargs):
    """
    Simple way to count the number of lines in a file with more options
    """
    if is_gziped(fp):
        open_fun = gzip.open
        open_mode =  "rt"
    else:
        open_fun = open
        open_mode =  "r"

    with open_fun(fp, open_mode) as fh:
        lines = 0
        for line in fh:
            if ignore_hashtag_line and line[0] == "#":
                continue
            lines += 1

    return lines

#~~~~~~~ DIRECTORY MANIPULATION ~~~~~~~#

def mkdir(fp, level=1, **kwargs):
    """
    Reproduce the ability of UNIX "mkdir -p" command
    (ie if the path already exits no exception will be raised).
    Can create nested directories by recursivity
    * fp
        path name where the folder should be created
    * level
        level in the path where to start to create the directories. Used by the program for the recursive creation of
        directories
    """

    # Extract the path corresponding to the current level of subdirectory and create it if needed
    fp = os.path.abspath(fp)
    split_path = fp.split("/")
    cur_level = split_path[level-1]
    cur_path = "/".join(split_path[0:level])
    if cur_path:
        _mkdir(cur_path)

    # If the path is longer than the current level continue to call mkdir recursively
    if len(fp.split("/")) > level:
        mkdir(fp, level=level+1)

def _mkdir (fp):
    if os.path.exists(fp) and os.path.isdir(fp):
        pass
    else:
        print ("Creating {}".format(fp))
        os.mkdir(fp)

def dir_walk (fp):
    """
    Print a directory arborescence
    """
    if os.path.exists(fp) and os.path.isdir(fp):
        if fp.endswith(os.sep):
            fp = fp[:-1]

        fp_len = len(fp.split(os.sep))
        for root, dirs, file_list in os.walk(fp):
            cur_path_len = len(root.split(os.sep)) - fp_len
            print((cur_path_len) * '-', os.path.basename(root))

            if file_list:
                file_list.sort()
                for f in file_list:
                    print((cur_path_len)*' ' + "-", f)


#~~~~~~~ SHELL MANIPULATION ~~~~~~~#

def make_cmd_str(
    prog_name,
    opt_dict={},
    opt_list=[],
    **kwargs):
    """
    Create a Unix like command line string from the prog name, a dict named arguments and a list of unmammed arguments
    exemple make_cmd_str("bwa", {"b":None, t":6, "i":"../idx/seq.fa"}, ["../read1", "../read2"])
    * prog_name
        Name (if added to the system path) or path of the program
    * opt_dict
        Dictionary of option arguments such as "-t 5". The option flag have to be the key (without "-") and the the
        option value in the dictionary value. If no value is requested after the option flag "None" had to be assigned
        to the value field.
    * opt_list
        List of simple command line arguments
    """

    # Start the string by the name of the program
    cmd = "{} ".format(prog_name)

    # Add options arguments from opt_dict
    if opt_dict:
        for key, value in opt_dict.items():
            if value:
                cmd += "{} {} ".format(key, value)
            else:
                cmd += "{} ".format(key)

    # Add arguments from opt_list
    if opt_list:
        for value in opt_list:
            cmd += "{} ".format(value)

    return cmd

def bash_basic(
    cmd,
    virtualenv=None,
    **kwargs):
    """
    Sent basic bash command
    * cmd
        A command line string formatted as a string
    * virtualenv
        If specified will try to load a virtualenvwrapper environment before runing the command
    """
    if virtualenv:
        cmd = "source ~/.bashrc && workon {} && {} && deactivate".format(virtualenv, cmd)
    with Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True) as proc:
        stdout, stderr = proc.communicate()
        print (stdout.decode())
        print (stderr.decode())

def bash(
    cmd,
    virtualenv=None,
    live="stdout",
    print_stdout=True,
    ret_stdout=False,
    log_stdout=None,
    print_stderr=True,
    ret_stderr=False,
    log_stderr=None,
    **kwargs):
    """
    More advanced version of bash calling with live printing of the standard output and possibilities to log the
    redirect the output and error as a string return or directly in files. If ret_stderr and ret_stdout are True a
    tuple will be returned and if both are False None will be returned
    * cmd
        A command line string formatted as a string
    * virtualenv
        If specified will try to load a virtualenvwrapper environment before runing the command
    * print_stdout
        If True the standard output will be LIVE printed through the system standard output stream
    * ret_stdout
        If True the standard output will be returned as a string
    * log_stdout
        If a filename is given, the standard output will logged in this file
    * print_stderr
        If True the standard error will be printed through the system standard error stream
    * ret_stderr
        If True the standard error will be returned as a string
    * log_stderr
        If a filename is given, the standard error will logged in this file
    """
    if virtualenv:
        cmd = "source ~/.bashrc && workon {} && {} && deactivate".format(virtualenv, cmd)

    #empty str buffer
    stdout_str = ""
    stderr_str = ""

    # First execute the command parse the output
    with Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE) as proc:

        # Only 1 standard stream can be output at the time stdout or stderr
        while proc.poll() is None:

            # Live parse stdout
            if live == "stdout":
                for line in iter(proc.stdout.readline, b''):
                    if print_stdout:
                        sys.stdout.write(line)
                    if ret_stdout or log_stdout:
                        stdout_str += line.decode()

            # Live parse stderr
            elif live == "stderr":
                for line in iter(proc.stderr.readline, b''):
                    if print_stderr:
                        sys.stderr.write(line)
                    if ret_stderr or log_stderr:
                        stderr_str += line.decode()

        # Verify that the command was successful and if not print error message and raise an exception
        if proc.returncode >= 1:
            sys.stderr.write("Error code #{} during execution of the command : {}\n".format(proc.returncode, cmd))
            sys.stderr.write(proc.stderr.read())
            return None

        if live != "stdout" and (print_stdout or ret_stdout or log_stdout):
            for line in iter(proc.stdout.readline, b''):
                if print_stdout:
                    sys.stdout.write(line)
                if ret_stdout or log_stdout:
                    stdout_str += line.decode()

        if live != "stderr" and (print_stderr or ret_stderr or log_stderr):
            for line in iter(proc.stderr.readline, b''):
                if print_stderr:
                    sys.stderr.write(line)
                if ret_stderr or log_stderr:
                    stderr_str += line.decode()

        # Write log in file if requested
        if log_stdout:
            with open (log_stdout, "w") as fp:
                fp.write(stdout_str)

        if log_stderr:
            with open (log_stderr, "w") as fp:
                fp.write(stderr_str)

    # Return standard output and err if requested
    if ret_stdout and ret_stderr:
        return (stdout_str, stderr_str)
    if ret_stdout:
        return stdout_str
    if ret_stderr:
        return stderr_str
    return None

def bash_update(cmd, update_freq=1, **kwargs):
    """
    FOR JUPYTER NOTEBOOK
    Run a bash command and print the output in the cell. The output is updated each time until the output is None.
    This is suitable for monitoring tasks that log events until there is nothing else to print such as bjobs or bpeeks.
    * cmd
        A command line string formatted as a string
    * update_freq
        The frequency of output updating in seconds [DEFAULT: 1]
    """

    # imports
    try:
        from IPython.core.display import clear_output
    except (NameError, ImportError) as E:
        print (E)
        print ("jupyter notebook is required to use this function. Please verify your dependencies")
        sys.exit()

    # Init stdout buffer
    stdout_prev= ""

    # Loop and update the line is something changes
    try:
        while True:
            stdout = bash(cmd, ret_stderr=False, ret_stdout=True, print_stderr=False, print_stdout=False)
            if stdout != stdout_prev:
                clear_output()
                print (stdout)
                stdout_prev = stdout
            if not stdout:
                print("All done")
                break

            time.sleep(update_freq)
    except KeyboardInterrupt:
        print("Stop monitoring\n")

def bsub (
    prog_cmd,
    virtualenv=None,
    mem=None,
    threads=None,
    queue=None,
    wait_jobid=None,
    stdout_fp=None,
    stderr_fp=None,
    send_email=False,
    print_full_cmd=True,
    dry=False,
    **kwargs):
    """
    FOR JUPYTER NOTEBOOK IN LSF environment
    Send an LSF bsub command through bash and return the JOBID
    For more information read the bsub documentation
    * prog_cmd
        A command line string formatted as a string
    * virtualenv
        If specified will try to load a virtualenvwrapper environment before runing the command
    * mem
        Memory to reserve (-M and -R 'rusage[mem=])
    * threads
        Number of thread to reserve (-n)
    * queue
        Name of the LSF queue to be used (-q)
    * wait_jobid
        jobid of list of jobid to wait before executing this command(-w 'post_done(jobid))
    * stdout_fp
        Path of the file where to write the standard output of the command (-oo)
    * stderr_fp
        Path of the file where to write the standard error of the command (-eo)
    * send_email
        If True, will force LSF to send an email even if stdout_fp and/or stderr_fp is given
    """
    bsub_cmd = "bsub "
    if mem:
        bsub_cmd += "-M {0} -R 'rusage[mem={0}]' ".format(mem)
    if threads:
        bsub_cmd += "-n {0} ".format (threads)
    if queue:
        bsub_cmd += "-q {0} ".format (queue)
    if stdout_fp:
        bsub_cmd += "-oo {0} ".format (stdout_fp)
    if stderr_fp:
        bsub_cmd += "-eo {0} ".format (stderr_fp)
    if send_email:
        bsub_cmd += "-N ".format (queue)
    if wait_jobid:
        if not type(wait_jobid) in (list, set, tuple):
            wait_jobid = [wait_jobid]
        jobid_str = "&&".join(["post_done({0})".format (jobid) for jobid in wait_jobid])
        bsub_cmd += "-w '{0}' ".format (jobid_str)

    cmd = f"{bsub_cmd} \"{prog_cmd}\""

    if print_full_cmd:
        print (cmd)
        return random.randint(1000000, 9999999)

    if not dry:
        stdout = bash (virtualenv=virtualenv, cmd=cmd, ret_stdout=True)
        jobid = stdout.split("<")[1].split(">")[0]
        return jobid

def bjobs_lock (update_freq=2, final_delay=5):
    """
    FOR JUPYTER NOTEBOOK IN LSF environment
    Check if bjobs has running or pending jobs until all are done
    * update_freq
        The frequency of output updating in seconds [DEFAULT: 2]
    * final_delay
        Final delay in seconds at the end of all jobs to prevent IO errors [DEFAULT: 5]
    """
    # Loop and update the line is something changes
    try:
        while True:
            time.sleep(update_freq)
            stdout = bash("bjobs", ret_stderr=False, ret_stdout=True, print_stderr=False, print_stdout=False)

            # Summarize active jobs
            pend = run = 0
            for s in stdout.split ("\n"):
                if s[:1].isdigit():
                    status = s.split()[2]
                    if status == "PEND":
                        pend+=1
                    elif status == "RUN":
                        run+=1
            stdout_print ("Running jobs:{} Pending jobs:{}\r".format(run, pend))

            if not stdout:
                stdout_print("All jobs done"+" "*30+"\n")
                stdout_print("Wait {}s for jobs to terminate\n".format(final_delay))
                time.sleep (final_delay)
                break

    except KeyboardInterrupt:
        stdout_print("User interuption"+" "*30+"\n")
        time.sleep (final_delay)


##~~~~~~~ DICTIONNARY FORMATTING ~~~~~~~#

def dict_to_md (
    d,
    key_label="",
    value_label="",
    transpose=False,
    sort_by_key=False,
    sort_by_val=True,
    max_items=None,
    **kwargs):
    """
    Transform a dict into a markdown formated table
    """
    # Preprocess dict
    if sort_by_key:
        d = OrderedDict(reversed(sorted(d.items(), key=lambda t: t[0])))

    if sort_by_val:
        d = OrderedDict(reversed(sorted(d.items(), key=lambda t: t[1])))

    if max_items and len(d)>max_items:
        d2 = OrderedDict()
        n = 0
        for key, value in d.items():
            d2[key]=value
            n+=1
            if n >= max_items:
                break
        d2["..."]="..."
        d=d2

    # Prepare output
    if transpose:
        buffer = "|{}|".format(key_label)
        for key in d.keys():
            buffer += "{}|".format(key)
        buffer += "\n|:---|"
        for _ in range(len(d)):
            buffer += ":---|"
        buffer += "\n|{}|".format(value_label)
        for value in d.values():
            buffer += "{}|".format(value)
        buffer += "\n"

    else:
        buffer = "|{}|{}|\n|:---|:---|\n".format(key_label, value_label)
        for key, value in d.items():
            buffer += "|{}|{}|\n".format(key, value)

    return buffer

def dict_to_report (
    d,
    tab="\t",
    ntab=0,
    sep=":",
    sort_dict=True,
    max_items=None,
    **kwargs):
    """
    Recursive function to return a text report from nested dict or OrderedDict objects
    """
    # Preprocess dict
    if sort_dict:

        # Verify that all value in the dict are numerical
        all_num = True
        for value in d.values():
            if not type(value) in [int, float]:
                all_num = False

        # Sort dict by val only if it contains numerical values
        if all_num:
            d = OrderedDict(reversed(sorted(d.items(), key=lambda t: t[1])))

            if max_items and len(d)>max_items:
                d2 = OrderedDict()
                n=0
                for key, value in d.items():
                    d2[key]=value
                    n+=1
                    if n >= max_items:
                        break
                d2["..."]="..."
                d=d2

        # Else sort alphabeticaly by key
        else:
            d = OrderedDict(sorted(d.items(), key=lambda t: t[0]))

    # Prepare output
    report = ""
    for name, value in d.items():
        if type(value) == OrderedDict or type(value) == dict:
            report += "{}{}\n".format(tab*ntab, name)
            report += dict_to_report(value, tab=tab, ntab=ntab+1, sep=sep, sort_dict=sort_dict, max_items=max_items)
        else:
            report += "{}{}{}{}\n".format(tab*ntab, name, sep, value)
    return report

##~~~~~~~ TABLE FORMATTING ~~~~~~~#

def reformat_table(
    input_file,
    output_file="",
    return_df=False,
    init_template=[],
    final_template=[],
    header = '',
    keep_original_header = True,
    header_from_final_template = False,
    replace_internal_space='_',
    replace_null_val="*",
    subst_dict={},
    filter_dict=[],
    predicate=None,
    standard_template=None,
    verbose=False,
    **kwargs):
    """
    Reformat a table given an initial and a final line templates indicated as a list where numbers
    indicate the data column and strings the formatting characters

    *  input_file
        A file with a structured text formatting (gzipped or not)
    *  output_file
        A file path to output the reformatted table (if empty will not write in a file)
    *  return_df
        If true will return a pandas dataframe containing the reformated table (Third party pandas package required)
        by default the columns will be names after the final template [DEFAULT:False]
    *  init_template
        A list of indexes and separators describing the structure of the input file
            Example initial line = "chr1    631539    631540    Squires|id1    0    +"
            Initial template = [0,"\t",1,"\t",2,"\t",3,"|",4,"\t",5,"\t",6]
            Alternatively, instead of the numbers, string indexes can be used, but they need to be enclosed in curly
            brackets to differentiate them from the separators. This greatly simplify the writing of the final template.
            Example initial line = "chr1    631539    631540    Squires|id1    0    +"
            Initial template = ["{chrom}","\t","{start}","\t","{end}","|","{name}","\t","{score}","\t","{strand}"]
    *  final_template
        A list of indexes and separators describing the required structure of the output file. Name indexes need to
        match indexes of the init_template and have to follow the same synthax  [DEFAULT:Same that init template]
            Example final line = "chr1    631539    631540    m5C|-|HeLa|22344696    -    -"
            Final template = [0,"\t",1,"\t",2,"\tm5C|-|HeLa|22344696\t-\t",6]
    *  header
        A string to write as a file header at the beginning of the file
    *  keep_original_header
        If True the original header of the input file will be copied at the beginning of the output file [DEFAULT:True]
    *  header_from_final_template
        Generate a header according to the name or number of the fields given in the final_template [DEFAULT:True]
    *  replace_internal_space
        All internal blank space will be replaced by this character [DEFAULT:"_"]
    *  replace_null_val
        Field with no value will be replaced by this character [DEFAULT:"*"]
    *  subst_dict
        Nested dictionary of substitution per position to replace specific values by others [DEFAULT:None]
            Example: { 0:{"chr1":"1","chr2":"2"}, 3:{"Squires":"5376774764","Li":"27664684"}}
    *  filter_dict
        A dictionary of list per position  to filter out lines  with specific values [DEFAULT:None]
            Example: { 0:["chr2", "chr4"], 1:["46767", "87765"], 5:["76559", "77543"]}
    *  predicate
        A lambda predicate function for more advance filtering operations [DEFAULT:None]
            Example:  lambda val_dict: abs(int(val_dict[1])-int(val_dict[2])) <= 2000
    *  standard_template
        Existing standard template to parse the file  instead of providing one manually. List of saved templates:
        - "gff3_ens_gene" = Template for ensembl gff3 fields. Select only the genes lines and decompose to individual elements.
        - "gff3_ens_transcript" = Template for ensembl gff3 fields. Select only the transcript lines and decompose to individual elements.
        - "gtf_ens_gene" = Template for ensembl gft fields. Select only the genes lines and decompose to individual elements
    * verbose
        If True will print detailed information [DEFAULT:False]
    """

    if verbose:
        print_arg()

    # Verify if the user provided a standard template and parameter the function accordingly
    # If needed the predicate2 variable will be used to filter the data according to the template
    if standard_template:

        if standard_template == "gff3_ens_gene":
            print("Using gff3 ensembl gene template. Non-gene features will be filtered out")

            init_template = ["{seqid}","\t","{source}","\t","{type}","\t","{start}","\t","{end}","\t","{score}","\t","{strand}","\t","{phase}",
            "\tID=","{ID}",
            ";gene_id=","{gene_id}",
            ";gene_type=","{gene_type}",
            ";gene_status=","{gene_status}",
            ";gene_name=","{gene_name}",
            ";level=","{level}",
            ";havana_gene=","{havana_gene}"]

            predicate2 = lambda v:v["type"]=="gene"

        if standard_template == "gtf_ens_gene":
            print("Using gtf ensembl gene template. Non-gene features will be filtered out")

            init_template = ["{seqid}","\t","{source}","\t","{type}","\t","{start}","\t","{end}","\t","{score}","\t","{strand}","\t","{phase}",
            "\tgene_id \"","{gene_id}",
            "\"; gene_type \"","{gene_type}",
            "\"; gene_status \"","{gene_status}",
            "\"; gene_name \"","{gene_name}",
            "\"; level ","{level}",
            "; havana_gene \"","{havana_gene}"]

            predicate2 = lambda v:v["type"]=="gene"

        if standard_template == "gff3_ens_transcript":
            print("Using gff3 ensembl transcript template. Non-transcript features will be filtered out")

            init_template = ["{seqid}","\t","{source}","\t","{type}","\t","{start}","\t","{end}","\t","{score}","\t","{strand}","\t","{phase}",
            "\tID=","{ID}",
            ";Parent=","{Parent}",
            ";gene_id=","{gene_id}",
            ";transcript_id=","{transcript_id}",
            ";gene_type=","{gene_type}",
            ";gene_status=","{gene_status}",
            ";gene_name=","{gene_name}",
            ";transcript_type=","{transcript_type}",
            ";transcript_status=","{transcript_status}",
            ";transcript_name=","{transcript_name}",
            ";level=","{level}",
            ";transcript_support_level=","{transcript_support_level}",
            ";tag=","{tag}",
            ";havana_gene=","{havana_gene}",
            ";havana_transcript=","{havana_transcript}"]

            predicate2 = lambda v:v["type"]=="transcript"

    else:
        predicate2 = None

    if not final_template:
        if verbose:
            print ("No final template given. Create final template from init template")
        final_template = init_template

    # Print the pattern of decomposition and recomposition
    if verbose:
        print ("Initial template values")
        print (_template_to_str(init_template))
        print ("Final template values")
        print (_template_to_str(final_template))

    #Init counters
    total = fail = success = filtered_out = 0

    # Init an empty panda dataframe if required
    if return_df:

    # Function specific third party import
        try:
            import pandas as pd
        except (NameError, ImportError) as E:
            print (E)
            print ("pandas is required to use this option. Please verify your dependencies")
            sys.exit()
        df = pd.DataFrame(columns = _template_to_list(final_template))

    # init empty handlers
    infile = outfile = None
    try:
        # open the input file gziped or not
        infile = gzip.open(input_file, "rt") if input_file[-2:].lower()=="gz" else open(input_file, "r")

        # open the output file if required
        if output_file:
            outfile = open (output_file, "wt")
            if header:
                outfile.write(header)
            if header_from_final_template:
                outfile.write(_template_to_str(final_template)+"\n")

        for line in infile:

            # Original header lines
            if line[0] == "#":
                # write in file if required
                if output_file:
                      if keep_original_header:
                        outfile.write(line)
                continue

            total+=1

            # Decompose the original line
            try:
                raw_val = _decompose_line(
                    line = line,
                    template = init_template)
                assert raw_val, "Decomposing the line #{} resulted in an empty value list:\n{}".format(total,line)
            except AssertionError as E:
                fail+=1
                continue

            # Filter and clean the values
            try:
                clean_val = _clean_values(
                    val_dict = raw_val,
                    replace_internal_space = replace_internal_space,
                    replace_null_val = replace_null_val,
                    subst_dict = subst_dict,
                    filter_dict = filter_dict,
                    predicate=predicate,
                    predicate2= predicate2)
                assert clean_val, "The line #{} was filter according to the filter dictionnary:\n{}".format(total,line)
            except AssertionError as E:
                filtered_out+=1
                continue

            # Fill the dataframe if needed
            if return_df:
                df.at[len(df)]= _reformat_list (val_dict=clean_val, template=final_template)

            # Recompose the line and write in file if needed
            if output_file:
                formated_line = _reformat_line (val_dict=clean_val, template=final_template)
                outfile.write(formated_line)

            success+=1

    # Close the files properly
    finally:
        if infile:
            infile.close()
        if outfile:
            outfile.close()

    if return_df:
        return df

    if verbose:
        print ("{} Lines processed\t{} Lines pass\t{} Lines filtered out\t{} Lines fail".format(total, success, filtered_out, fail))

def _is_str_key (element):
    return type(element)==str and element[0]=="{" and element[-1]=="}"

def _is_str_sep (element):
    return type(element)==str and (element[0]!="{" or element[-1]!="}")

def _template_to_str(template):
    l=[]
    for element in template:
        if _is_str_sep(element):
            l.append(element)
        elif _is_str_key(element):
            l.append(element[1:-1])
        elif type(element) == int:
            l.append(str(element))
    return "".join(l)

def _template_to_list(template):
    l=[]
    for element in template:
        if _is_str_key(element):
            l.append(element[1:-1])
        elif type(element) == int:
            l.append(str(element))
    return l

def _decompose_line(line, template):
    """Helper function for reformat_table. Decompose a line in a dictionnary and extract the values given a template list"""

    val_dict = OrderedDict()

    # Remove the first element from the line if this is a separator
    if _is_str_sep(template[0]):
        val, sep, line = line.partition(template[0])
        template = template[1:]

    # Decompose the line
    last_key = None
    for element in template:
        # if found a str key, store it and remove the curly brackets
        if _is_str_key(element):
            last_key = element[1:-1]
        # if numerical key, just store it
        if type(element) == int:
            last_key = element
        if _is_str_sep(element):
            # Verify the values before filling the dict
            assert last_key != None, "Problem in the init template"
            assert last_key not in val_dict, "Duplicated key in the init template"
            val, sep, line = line.partition(element)
            val_dict[last_key] = val
            last_key = None

    # Manage last element of the template if it is a key
    if last_key:
        val_dict[last_key] = line

    return val_dict

def _clean_values (
    val_dict,
    replace_internal_space=None,
    replace_null_val=None,
    subst_dict={},
    filter_dict={},
    predicate=None,
    predicate2=None):
    """Helper function for reformat_table. Clean the extracted values"""

    for key in val_dict.keys():
        # Strip the heading and trailing blank spaces
        val_dict[key] = val_dict[key].strip()

        # Replace the empty field by a given char
        if replace_null_val and not val_dict[key]:
            val_dict[key] = replace_null_val

        # Replace internal spaces by underscores
        if replace_internal_space:
            val_dict[key] = val_dict[key].replace(" ","_")

        # Filter line based on the filter_dict
        if key in filter_dict and val_dict[key] in filter_dict[key]:
            return None

        # Filter line base on predicate function
        if predicate and not predicate(val_dict):
            return None

        # Filter line base on an eventual second predicate function
        if predicate2 and not predicate2(val_dict):
            return None

        # Use the substitution dict exept if the value is not in the dict in this case use the default value
        if key in subst_dict and val_dict[key] in subst_dict[key]:
            val_dict[key] = subst_dict[key][val_dict[key]]

    return val_dict

def _reformat_line (val_dict, template):
    """Helper function for reformat_table. Reassemble a line from a dict of values and a template list"""

    line = ""
    try:
        for element in template:
            if _is_str_sep(element):
                line+=element
            elif type(element) == int:
                line+=val_dict[element]
            elif _is_str_key(element):
                line+=val_dict[element[1:-1]]

    except IndexError as E:
        print (E)
        print (val_dict)
        print (template)
        raise

    return line+"\n"

def _reformat_list (val_dict, template):
    """Helper function for reformat_table. Reassemble a list from a dict of values and a template list"""

    l=[]
    try:
        for element in template:
            if type(element) == int:
                l.append(val_dict[element])
            elif _is_str_key(element):
                l.append(val_dict[element[1:-1]])

    except IndexError as E:
        print (E)
        print (val_dict)
        print (template)
        raise

    return l

##~~~~~~~ WEB TOOLS ~~~~~~~#

def url_exist (url, **kwargs):
    """
    Predicate verifying if an url exist without downloading all the link
    """

    # Function specific third party import
    try:
        import httplib2
    except (NameError, ImportError) as E:
        print (E)
        print ("httplib2 is required to use this function. Please verify your dependencies")
        sys.exit()

    # Chek the url
    h = httplib2.Http()

    try:
        resp = h.request(url, 'HEAD')
        return int(resp[0]['status']) < 400
    except:
        return False

def wget(url, out_name="", progress_block=100000000, **kwargs):
    """
    Download a file from an URL to a local storage.
    *  url
        A internet URL pointing to the file to download
    *  outname
        Name of the outfile where (facultative)
    *  progress_block
        size of the byte block for the progression of the download
    """

    def size_to_status (size):
        if size >= 1000000000:
            status = "{} GB".format(round(size/1000000000, 1))
        elif size >= 1000000:
            status = "{} MB".format(round(size/1000000, 1))
        elif size >= 1000:
            status = "{} kB".format(round(size/1000, 1))
        else :
            status = "{} B".format(size)
        return status

    # Function specific standard lib imports
    from urllib.request import urlopen
    from urllib.parse import urlsplit
    from urllib.error import HTTPError, URLError

    # Open the url and retrieve info
    try:
        u = urlopen(url)
        scheme, netloc, path, query, fragment = urlsplit(url)
    except (HTTPError, URLError, ValueError) as E:
        print (E)
        return None

    # Attribute a file name if not given
    if not out_name:
        out_name = file_name(path)
        if not out_name:
            out_name = 'output.file'

    # Create the output file and
    with open(out_name, 'wb') as fp:

        # Retrieve file meta information
        meta = u.info()
        meta_func = meta.getheaders if hasattr(meta, 'getheaders') else meta.get_all
        meta_size = meta_func("Content-Length")
        if meta_size:
            file_size = int(meta_func("Content-Length")[0])
            print("Downloading: {}\tBytes: {}".format(url, file_size))
        else:
            file_size=None
            print("Downloading: {}\tSize unknown".format(url))

        # Buffered reading of the file to download
        file_size_dl = 0
        block_sz = 1000000

        last_pblock = progress_block
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break
            fp.write(buffer)

            # Progress bar
            file_size_dl += len(buffer)

            if file_size_dl >= last_pblock:
                status = "{} Downloaded".format(size_to_status(file_size_dl))
                if file_size:
                    status += "\t[{} %]".format (round(file_size_dl*100/file_size, 2))
                print(status)
                last_pblock += progress_block

        # Final step of the progress bar
        status = "{} Downloaded".format(size_to_status(file_size_dl))
        if file_size:
            status += "\t[100 %]"
        print(status)

    return out_name

##~~~~~~~ FUNCTIONS TOOLS ~~~~~~~#

def print_arg(**kwargs):
    """
    Print calling function named and unnamed arguments
    """

    # Function specific standard lib imports
    from inspect import getargvalues, stack

    # Parse all arg
    posname, kwname, args = getargvalues(stack()[1][0])[-3:]
    # For enumerated named arguments
    if args:
        print("Enumerated named argument list:")
        for i, j in args.items():
            if i != posname and i != kwname:
                print("\t{}: {}".format(i,j))
        # For **kwarg arguments
        if kwname:
            print("Unenumerated named arguments list:")
            for i, j in args[kwname].items():
                print("\t{}: {}".format(i,j))
        args.update(args.pop(kwname, []))
        if posname:
            print("Unnamed positional arguments list:")
            for i in args[posname]:
                print("\t{}".format(i))

##~~~~~~~ SSH TOOLS ~~~~~~~#

def scp (
    hostname,
    local_file,
    remote_dir,
    username=None,
    rsa_private_key=None,
    ssh_config="~/.ssh/config",
    verbose=False,
    **kwargs):
    """
    Copy a file over ssh in a target remote directory
    * hostname
        Name of the host ssh server
    * username
        name of the user
    * rsa_private_key
        path to the rsa private key
    * local_file
        path to the local file
    * remote_dir
        path to the target directory
    * ssh_config
        use as an alternative method instead of giving the username and rsa_private_key. Will fetch them from the config file directly
    """
    # Function specific third party import
    try:
        import paramiko
    except (NameError, ImportError) as E:
        print (E)
        print ("paramiko is required to use this function. Please verify your dependencies")
        sys.exit()

    if not username or not rsa_private_key:
        if verbose: print ("Parse the ssh config file")
        ssh_config = os.path.expanduser(ssh_config)
        # Find host in the host list of the ssh config file
        with open (ssh_config) as conf:
            host_dict = OrderedDict()
            host=None
            for line in conf:
                if not line.startswith("#"):
                    if line.startswith("Host"):
                        host = line.strip().split()[1]
                        host_dict[host] = OrderedDict()
                    else:
                        ls = line.strip().split()
                        if len(ls) == 2:
                            host_dict[host][ls[0]]= ls[1]

        try:
            username = host_dict[hostname]["User"]
            rsa_private_key = os.path.expanduser(host_dict[hostname]["IdentityFile"])
            hostname = host_dict[hostname]["Hostname"]
        except KeyError as E:
            print(E)
            print('Hostname not found in the config file or config not containing User, IdentityFile and Hostname')
            raise

    # now, connect and use paramiko Transport to negotiate SSH2 across the connection
    if verbose: print ('Establishing SSH connection to: {} ...'.format(hostname))
    with paramiko.Transport(hostname) as t:
        t.start_client()

        try:
            key = paramiko.RSAKey.from_private_key_file(rsa_private_key)
            t.auth_publickey(username, key)
            if verbose: print ('... Success!')

        except Exception as e:
            if verbose: print ('... Failed loading {}'.format(rsa_private_key))

        assert t.is_authenticated(), 'RSA key auth failed!'

        sftp = t.open_session()
        sftp = paramiko.SFTPClient.from_transport(t)

        if remote_dir.startswith ("~"):
            remote_dir = "."+remote_dir[1:]

        try:
            sftp.mkdir(remote_dir)
            if verbose: print ('Create directory {}'.format(remote_dir))
        except IOError as e:
            if verbose: print ('Assuming {} exists'.format(remote_dir))

        remote_file = remote_dir + '/' + os.path.basename(local_file)

        if verbose: print ('Copying local file from {} to {}:{}'.format(local_file, hostname, remote_file))
        sftp.put(local_file, remote_file)
        if verbose: print ('All operations complete!')

##~~~~~~~ PACKAGE TOOLS ~~~~~~~#

def get_package_file (package, fp="", **kwargs):
    """
    Verify the existence of a file from the package data and return a file path
    * package
        Name of the package
    * fp
        Relative path to the file in the package. Usually package_name/data/file_name
        if the path points to a directory the directory arborescence will be printed
    """
    # Try to import pkg_resources package and try to get the file via pkg_resources
    try:
        from pkg_resources import Requirement, resource_filename, DistributionNotFound
        fp = resource_filename(Requirement.parse(package), fp)
    except (NameError, ImportError, DistributionNotFound) as E:
        warnings.warn(str(E))
        return

    # if the path exists
    if os.path.exists(fp):

        # In case no fp is given or if the path is a directory list the package files, print the arborescence
        if os.path.isdir(fp):
            for root, dirs, files in os.walk(fp):
                path = root.split(os.sep)
                print((len(path) - 1) * '-', os.path.basename(root))
                for file in files:
                    print(len(path) * '-', file)
            return fp

        # If file exist and is readable
        if os.access(fp, os.R_OK):
            return fp

    else:
        warnings.warn("File does not exist or is not readeable")
        return

##~~~~~~~ SAM/BAM TOOLS ~~~~~~~#

def bam_sample(fp_in, fp_out, n_reads, verbose=False, **kwargs):
    """
    Sample reads from a SAM/BAM file and write in a new file
    * fp_in
        Path to the input file in .bam/.sam/.cram (the format will be infered from extension)
    * fp_out
        Path to the output file in .bam/.sam/.cram (the format will be infered from extension)
    * n_reads
        number of reads to sample
    """
    # Function specific third party import
    try:
        import pysam as ps
    except (NameError, ImportError) as E:
        warnings.warn ("pysam is required to use this function. Please verify your dependencies")
        return

    # Define opening mode
    if has_extension(fp_in, "bam"):
        mode_in = "rb"
    elif has_extension(fp_in, "sam"):
        mode_in = "r"
    elif has_extension(fp_in, "cram"):
        mode_in = "rc"
    else:
        warnings.warn ("Invalid input file format (.bam/.sam/.cram)")
        return
    if has_extension(fp_out, "bam"):
        mode_out = "wb"
    elif has_extension(fp_out, "sam"):
        mode_out = "w"
    elif has_extension(fp_out, "cram"):
        mode_out = "wc"
    else:
        warnings.warn ("Invalid output file format (.bam/.sam/.cram)")
        return

    # Count the reads and define a list of random lines to sample
    with ps.AlignmentFile(fp_in, mode_in) as fh_in:
        n_read_origin = fh_in.count()
        if verbose:
            print("Found {} reads in input file".format(n_read_origin))

        # Take into account the situation in which there are less lines in the file than requested.
        if n_reads >= n_read_origin:
            if verbose:
                print("Not enough lines in source file. Writing all reads in the output file")
            index_list = list(range(0, n_read_origin-1))
        else:
            index_list = sorted(random.sample(range(0, n_read_origin-1), n_reads))

    # Sample lines in input file according to the list of random line numbers
    with ps.AlignmentFile(fp_in, mode_in) as fh_in:
        with ps.AlignmentFile(fp_out, mode_out, header=fh_in.header) as fh_out:
            j = 0
            for i, line in enumerate(fh_in):
                if j >= n_reads:
                    break
                if i == index_list[j]:
                    fh_out.write(line)
                    j+=1
            if verbose:
                print("Wrote {} reads in output file".format(j))

##~~~~~~~ DNA SEQUENCE TOOLS ~~~~~~~#

def base_generator (
    bases = ["A","T","C","G"],
    weights = [0.280788,0.281691,0.193973,0.194773],
    **kwargs):
    """
    Generator returning DNA/RNA bases according to a probability weightning
    * bases: list (default ["A","T","C","G"])
        DNA RNA bases allowed
    * weights: list (default [0.280788,0.281691,0.193973,0.194773])
        Probability of each base to be returned. Should match the index of bases. The sum does not need to be equal to 1.
        If the list is empty bases will be returned with a flat probability. The default values represent the frequency in the human
        genome (excluding N).
    """
    # If weights is provided create weighted generator
    if weights:

        # Verify that the 2 lists are the same size
        if len(bases) != len(weights):
            raise ValueError ("weights is not the same length as bases.")

        # Calculate cumulated weights
        cum_weights = list(itertools.accumulate(weights))

        while True:
            # Emit a uniform probability between 0 and the max value of the cumulative weigths
            p = random.uniform(0, cum_weights[-1])
            # Use bisect to retun the corresponding base
            yield bases[bisect.bisect(cum_weights, p)]

    # If not weight if required, will return each base with the same probability
    else:
        while True:
            yield random.choice(bases)

def make_sequence (
    bases = ["A","T","C","G"],
    weights = [0.280788,0.281691,0.193973,0.194773],
    length=1000,
    **kwargs):
    """
    return a sequence of DNA/RNA bases according to a probability weightning
    * bases: list (default ["A","T","C","G"])
        DNA RNA bases allowed in the sequence
    * weights: list (default [0.280788,0.281691,0.193973,0.194773])
        Probability of each base to be returned. Should match the index of bases. The sum does not need to be equal to 1.
        If the list is empty bases will be returned with a flat probability. The default values represent the frequency in the human
        genome (excluding N).
    * length: int (default 1000)
        length of the sequence to be returned
    """
    bgen = base_generator(bases=bases, weights=weights)
    seq_list = [next(bgen) for _ in range (length)]
    return "".join(seq_list)
