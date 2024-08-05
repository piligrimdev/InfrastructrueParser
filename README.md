# Infrastructure parser

Parser of *WinAudit*, *ScanOVAL* and *DrawIO* files, combining data in single *json* file.

# How To Use

## Quick start
```
python main.py -inDir <Path to input directory>
```
Script will scan `-inDir` directory for `.drawio`(`.xml`) file and nested directories for _scanOVAl_ and _WinAudit_ `.html` files. ```result.json``` will be saved in ```-inDir``` directory.

### Input directory structure example

```
├── inputDir
│   ├── 113
│   │   ├── scanoval.html
│   │   ├── winaudit.html
│   ├── 233
│   │   ├── winaudit.html
│   ├── directory_name
│   │   ├── scanoval.html
│   ├── diagram.drawio
```

> Note that `id` for server with files in directory `inputDir/directory_name` will be generated automatically, but for servers with files in `inputDir/113`  and `inputDir/233` `id`'s will be **113** and **233** respectively.

___
## Keys usage

```
usage: WinAudit parser [-h] -inDir INDIR [-outDir OUTDIR] [-servers-template SERVERS_TEMPLATE]
                       [-drawio-template DRAWIO_TEMPLATE] [-result-template RESULT_TEMPLATE]

options:
  -h, --help            show this help message and exit

required arguments:
  -inDir INDIR          Path to directory containing drawio .xml file and directoires with winaudit and scanoval .html
                        files

optional arguments:
  -outDir OUTDIR        Path to output directory for resulting .json file
  
  -servers-template SERVERS_TEMPLATE
                        Path to servers parsing template (.json)
                        
  -drawio-template DRAWIO_TEMPLATE
                        Path to drawio parsing template (.json)
                        
  -result-template RESULT_TEMPLATE
                        Path to result template (.json)
```
___
## Templates usage

### Servers template structure example

```json
{
    "templates": [
        {
            "section_name": "blank section name",
            "type": "blank",
            "html_section_name": "",
            "template": {
                "server_key_name": ""
            }
        },
        {
            "section_name": "ip",
            "type": "list",
            "html_section_name": "Network Adapters",
            "template": {
                "address": "IP Address",
                "netmask": "IP Subnet"
            }
        },
        {
            "section_name": "any name",
            "type": "head",
            "html_section_name": "Обзор системы",
            "template": {
                "name": "Computer Name"
            }
        }
    ]
}
```

Script looks for tables in *WinAudit* file named `"html_section_name"` and maps
 rows to template keys.
#### Example:
 
* In *WinAudit* file, **table** named `"Network Adapters"` has **row** `"IP Address"` with **value** `"0.0.0.0"`
* Template file has `"template"` object with `"section_name": "ip"` **key-value pair**
* `"ip"`'s `"template"` object maps `"IP Address"` to `"address"`
* `"server"` object in result file will have `"ip"` object with `"address": "0.0.0.0"` **key-value pair**

#### Types descriptions
* `"type: "head"` template will add values directly to `"server"` object. 
* `"type: "list"` template will add a list named `"section_name"` with `"template"` objects.
* Script adds `"type": "blank"`  template as empty list named `"section_name"`. 

> Script can map many tables to one section in server object. Just add `"template"` object with equal `"section_name"` and different `"html_section_name"` to `"templates"` list.

### Drawio parse template structure example
```json
{
    "figures_recognition": {
        "hardware": {
            "param": "rounded",
            "value": "0"
        },
        "external_media": {
            "param": "shape",
            "value": "cylinder3"
        },
        "shd": {
            "param": "rhombus",
            "value": ""
        }
    },
    "figures_text_mapping": {
        "hardware": {
            "name": "name",
            "tag": "tag",
            "Model": "model",
            "servers": "servers"
        },
        "external_media": {
            "name": "name",
            "tag": "tag",
            "type": "type"
        },
        "shd": {
            "name": "name",
            "tag": "tag",
            "type": "type"
        }
    }
}
```

Script uses `"figures_recognition"` object to map infrastructure objects types to shapes in `.drawio` file.


* If `"value"` is **empty string**, script will map any shape that has `"param"` value in `<style>` attributes.
* If `"value"` has **string value**, script will map shape that has `"param"` with value `"value"` in `<style>` attributes.

> Consider using shapes with non-overlapping  `<style>` attributes to proper mapping.

Script uses `"figures_text_mapping"` object to retrieve data from shapes and map it to segment objects <br>
In  `"figures_text_mapping"` objects:
* **Key** represents key of **segment** object
* **Value** represents key of shape data. **Segment** objects then will have shape's data values.


> **Keys of `"figures_recognition"` and `"figures_text_mapping"` must be equal.**




#### Example:

* Shape "Rectangle" has data:
    ```
    name: super name;
    tag: cool tag;
    model: awesome model;     
    ```
* `"figures_recognition"` has object `"hardware"`:
    ```json
    "hardware": {
            "param": "rounded",
            "value": "0"
        }
    ```
* `"figures_text_mapping"` has object `"hardware"`:
    ```json
     "hardware": {
            "name": "name",
            "tag": "tag",
            "Model": "model",
            "servers": "servers"
        }
    ```
* In resulting file, "`hardware`" list will have object with key-value pairs:
    ```json
    {
        "name": "super name",
        "tag": "cool tag",
        "SN": "string", // Default segment value
        "Model": "awesome model",
        "OS_apply": true, // Default segment value
        ...
    }
    ```

### Drawio file structure
**Data in shapes should match following regular expression:** 
```
^([а-яА-ЯёЁ\w\-\_\@\s]+:\s*(([а-яА-ЯёЁ\w\-\_\@\s]+)|(\[([0-9]+,*)+\]))\s*;)+$
```
 
**I.e. text in shapes should look like:**
```
key: value; 
other key: other_value;
```

May contain list of numeric values (`"id"`'s of servers for `"hardware"` objects) 
```
servers: [1,2,3];
```

### Result file structure

*To be completed*