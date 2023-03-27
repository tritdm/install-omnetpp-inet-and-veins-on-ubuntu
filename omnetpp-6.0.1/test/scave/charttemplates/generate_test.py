#!/usr/bin/env python3

import os
import sys
import re

from omnetpp.scave.analysis import *
from omnetpp.scave.charttemplate import *

skeleton = """
# generated by {tester}

def chart_script():
{script}

try: import testlib
except: pass

if 'testlib' in dir():
    testlib.run_test(chart_script, {name}, {desc}, {errmsg})
else:
    print('testlib not available, running chart script without it')
    chart_script()
"""
# Command-line args are interpreted as as words to filter for. We try to match whole numbers, i.e. "foo1", "2bar" should not match "foo10", "foo123", "42bar", etc.
test_filter = [re.compile((r"(^|[^\d])" if re.match(r"^\d",arg) else "") + arg + (r"($|[^\d])" if re.match(r"\d$",arg) else "")) for arg in sys.argv[1:]]

def make_charts(template_ids, group, base_props, tests):
    def indent(s):
        return "\n".join(["    " + l for l in s.splitlines()])

    global templates
    charts = []
    for template_id in template_ids:
        template = templates[template_id]
        i = 0
        for case in tests:
            propname = case['key']
            propvalues = case['value']
            errmsg = case['errmsg'] if 'errmsg' in case else None
            extra_props = case['props'] if 'props' in case else {}
            template_filter = case['only_for'] if 'only_for' in case else None
            if template_filter and type(template_filter) != list:
                template_filter = [ template_filter ]
            if template_filter and template_id not in template_filter:
                continue

            if type(propvalues) != list:
                propvalues = [ propvalues ]
            for propvalue in propvalues:
                name = template_id + "_" + group + "_" + str(i)
                desc = "{}={}".format(propname, repr(propvalue)) if propname else "base"
                if extra_props:
                    desc += ", when " + ", ".join(["{}={}".format(k, repr(v)) for k,v in extra_props.items()])
                desc = desc.replace("$", "\\$")  # otherwise Matplotlib interprets them as LaTeX math notation
                i += 1
                props = base_props.copy()
                if extra_props:
                    props.update(extra_props)
                if propname:
                    props.update({propname: propvalue})

                #print([regex.search(name+" "+desc) for regex in test_filter])
                if test_filter and not all(regex.search(name+" "+desc) for regex in test_filter):
                    continue

                chart = template.create_chart(name=name + " " + desc, props=props)
                chart.script = skeleton.format(tester=__file__, script=indent(chart.script), name=repr(name), desc=repr(desc), errmsg=repr(errmsg))
                charts.append(chart)
    return charts

templates = load_chart_templates()
charts = []

def case(key=None, value=None, errmsg=None, props=None, only_for=None):
    return locals()  # convert to a dict

legend_placement_inside = ["best", "upper right", "upper left", "lower left", "lower right", "right", "center left", "center right", "lower center", "upper center", "center"]
legend_placement_outside = ["outside top left", "outside top center", "outside top right", "outside bottom left", "outside bottom center", "outside bottom right", "outside left top", "outside left center", "outside left bottom", "outside right top", "outside right center", "outside right bottom"]

charts += make_charts(
    ["barchart_native", "barchart_mpl", "linechart_native", "linechart_mpl", "linechart_separate_mpl",
    "scatterchart_itervars_native", "scatterchart_itervars_mpl", "histogramchart_native", "histogramchart_mpl",
    "histogramchart_vectors_native", "histogramchart_vectors_mpl", "3dchart_itervars_mpl", "boxwhiskers"],
    "wrongfilter",
    {},
    [
        case("filter", "", errmsg="Error while querying results: Empty filter expression"),
        case("filter", "aa bb", errmsg="Syntax error"),
        case("filter", "nonexistent OR whatever", errmsg="returned no data"),
    ]
)

charts += make_charts(
    ["barchart_native", "barchart_mpl"],
    "data",
    {
        "filter": "runattr:experiment =~ PureAlohaExperiment AND name =~ channelUtilization:last",
    },
    [
        # everything is default
        case(None, None),

        # different filters
        case("filter", "runattr:experiment =~ PureAlohaExperiment AND type =~ scalar", props={"groups": "iaMean", "series": "numHosts"}),
        case("filter", "runattr:experiment =~ PureAlohaExperiment AND name =~ channel*", props={"groups": "iaMean", "series": "numHosts"}),

        # automatic groups and series inference
        case("filter", "runattr:experiment =~ PureAlohaExperiment AND type =~ scalar"),
        case("filter", "runattr:experiment =~ PureAlohaExperiment AND name =~ channel*"),

        case("groups", "iaMean", props={"series": "numHosts"}),
        case("groups", "numHosts", props={"series": "numHosts"}, errmsg="Overlap between Group and Series columns"),
        case("groups", "experiment", props={"series": "numHosts"}),
        case("groups", "measurement", props={"series": "name", "xlabel_rotation": "-30"}),
        case("groups", "name", props={"series": "numHosts"}),
        case("groups", "aa bb", props={"series": "numHosts"}, errmsg="No such iteration variable"),
        case("groups", "", props={"series": "numHosts"}, errmsg="set both the Groups and Series properties"),

        case("series", "iaMean", props={"groups": "iaMean"}, errmsg="Overlap between Group and Series columns"),
        case("series", "experiment", props={"groups": "iaMean"}),
        case("series", "measurement", props={"groups": "name"}),
        case("series", "name", props={"groups": "iaMean"}),
        case("series", "aa bb", props={"groups": "iaMean"}, errmsg="No such iteration variable"),
        case("series", "", props={"groups": "iaMean"}, errmsg="set both the Groups and Series properties"),
    ]
)

charts += make_charts(
    ["barchart_native", "barchart_mpl"],
    "styling",
    {
        "filter": "runattr:experiment =~ PureAlohaExperiment AND name =~ channelUtilization:last",
        "groups": "iaMean",
        "series": "numHosts",
    },
    [
        # bars
        case("baseline", "10"),
        case("bar_placement", ["Aligned", "Overlap", "InFront", "Stacked"]),

        # grid
        case("grid_show", "false"),
        case("grid_density", ["Major", "All"]),

        # legend
        case("legend_show", "false"),
        case("legend_placement", legend_placement_inside, only_for="barchart_mpl"),
        case("legend_placement", legend_placement_inside + legend_placement_outside, only_for="barchart_native"),

        # legend labels
        case("legend_prefer_result_titles", "false", props={"legend_automatic":"true"}),
        case("legend_prefer_module_display_paths", "false", props={"legend_automatic":"true"}),
        case("legend_format", "$name in $module", props={"legend_automatic":"false"}),
        case("legend_replacements", "/ /_/\n/:/->/\n/=/==/", props={"legend_automatic":"true"}),
        case("legend_replacements", "/ /_/\n/:/->/\n/=/==/", props={"legend_automatic":"false", "legend_format":"$name in $module"}),

        # axes
        case("xaxis_title", "Manual X Axis Title"),
        case("yaxis_title", "Manual Y Axis Title"),
        case("yaxis_min", "0.1"),
        case("yaxis_max", "0.1"),
        case("yaxis_log", "true"),
        case("xlabel_rotation", "30"),

        # styling
        case("Plot.BackgroundColor", "yellow", only_for="barchart_native"),
        # <property name="cycle_seed" value="0"/>
        case("Plot.Title.Font", "Arial-regular-20", only_for="barchart_native"),
        case("Axis.Title.Font", "Arial-regular-20", only_for="barchart_native"),
        case("Axis.Label.Font", "Arial-regular-20", only_for="barchart_native"),
        case("Legend.Font", "Arial-regular-20", only_for="barchart_native"),
        case("Legend.Border", "true", only_for="barchart_native"),
        # <property name="X.Label.Wrap" value="true"/>
    ]
)

charts += make_charts(
    ["linechart_native", "linechart_mpl", "linechart_separate_mpl"],
    "base",
    {
        "filter": "runattr:experiment =~ Fifo* AND name =~ qlen:vector",
        "vector_start_time": "1",
        "vector_end_time": "4",
    },
    [
        case(None, None),
        case(None, None, props={"vector_start_time": "", "vector_end_time": ""}),
        case(None, None, props={"vector_start_time": "5", "vector_end_time": ""}),
        case(None, None, props={"vector_start_time": "", "vector_end_time": "10"}),
        case("vector_start_time", ["","1e6"]),
        case("vector_end_time", ["", "0"]),

        case("vector_operations", ["apply:mean","compute:sum"]),
        case("vector_operations", "apply:sum #comment\napply:timeshift(100) # comment"),

        # TODO: uncomment when there is better error reporting
        case("vector_operations", "apply:nonexistent", errmsg="Vector filter function 'nonexistent' not found"),
        case("vector_operations", "apply:timeshift(invalidparam=6.5)", errmsg="timeshift() got an unexpected keyword argument 'invalidparam'"),
    ]
)

charts += make_charts(
    ["linechart_native", "linechart_mpl", "linechart_separate_mpl"],
    "styling",
    {
        "filter": "runattr:experiment =~ TandemQueueExperiment AND name =~ qlen:vector AND module =~ *.fifo1 AND runattr:replication =~ #0",
        "vector_end_time": "50",
        "vector_operations": "compute:timeavg(interpolation='sample-hold')",
    },
    [
        # axes
        case("xaxis_title", "Manual X Axis Title"),
        case("yaxis_title", "Manual Y Axis Title"),
        case("xaxis_min", "20"),
        case("xaxis_max", "20"),
        case("yaxis_min", "1.5"),
        case("yaxis_max", "1.5"),
        case("xaxis_log", "true"),
        case("yaxis_log", "true"),

        # grid
        case("grid_show", "false"),
        case("grid_density", ["Major", "All"]),

        # legend
        case("legend_show", "false"),
        case("legend_placement", legend_placement_inside, only_for=["linechart_mpl", "linechart_separate_mpl"]),
        case("legend_placement", legend_placement_inside + legend_placement_outside, only_for="linechart_native"),

        # legend labels
        case("legend_prefer_result_titles", "false", props={"legend_automatic":"true"}),
        case("legend_prefer_module_display_paths", "false", props={"legend_automatic":"true"}),
        case("legend_format", "$name in $module", props={"legend_automatic":"false"}),
        case("legend_replacements", "/ /_/\n/:/->/\n/=/==/", props={"legend_automatic":"true"}),
        case("legend_replacements", "/ /_/\n/:/->/\n/=/==/", props={"legend_automatic":"false", "legend_format":"$name in $module"}),

        # lines
        case("drawstyle", ["auto", "none", "linear", "steps-pre", "steps-mid", "steps-post"], props={"marker":"."}),
        case("drawstyle", ["none"], props={"marker":"."}),
        case("linecolor", ["", "green", "#808080"]),
        case("linestyle", ["none", "solid", "dotted", "dashed", "dashdot"]),
        case("linewidth", ["0", "0.5", "1", "5"]),

        # markers
        case("marker", ["auto", "none", ". (dot)", *list(".,^v")], props={"drawstyle":"none"}),  # more: ".,v^<>1234|_8osp*xDd"
        case("markersize", ["3","10"], props={"marker":".", "drawstyle":"none"}),

        # misc
        case("plt.style", ["default", "ggplot", "grayscale", "seaborn"], only_for=["linechart_mpl", "linechart_separate_mpl"]),
        case("cycle_seed", ["0", "1"], None)
    ]
)

charts += make_charts(
    ["scatterchart_itervars_native", "scatterchart_itervars_mpl"],
    "all",
    {
        "filter": "runattr:experiment =~ PureAlohaExperiment AND name =~ channelUtilization:last",
        "xaxis_itervar": "iaMean",
        "group_by": "numHosts"
    },
    [
        case(None, None),
        case("filter", "runattr:experiment =~ PureAlohaExperiment AND type =~ scalar"),
        case("filter", "runattr:experiment =~ PureAlohaExperiment AND name =~ channel*"),

        case("xaxis_itervar", "iaMean"),
        case("xaxis_itervar", "numHosts", errmsg="X axis column also in grouper columns:"),
        case("xaxis_itervar", "experiment"),
        case("xaxis_itervar", "name"),
        case("xaxis_itervar", "aa bb", errmsg="iteration variable for the X axis could not be found"),
        case("xaxis_itervar", "", errmsg="select the iteration variable for the X axis"),

        case("group_by", "iaMean", errmsg="X axis column also in grouper columns:"),
        case("group_by", "numHosts"),
        case("group_by", "numHosts, replication"),
        case("group_by", "experiment"),
        case("group_by", "name"),
        case("group_by", "aa bb", errmsg="iteration variable for grouping could not be found"),
        case("group_by", ""),

        # axes
        case("xaxis_title", "Manual X Axis Title"),
        case("yaxis_title", "Manual Y Axis Title"),
        case("xaxis_min", "3"),
        case("xaxis_max", "5"),
        case("yaxis_min", "0.1"),
        case("yaxis_max", "0.15"),
        case("xaxis_log", "true"),
        case("yaxis_log", "true"),

        # grid
        case("grid_show", "false"),
        case("grid_density", ["Major", "All"]),

        # legend
        case("legend_show", "false"),
        case("legend_placement", legend_placement_inside, only_for=["linechart_mpl", "linechart_separate_mpl"]),
        case("legend_placement", legend_placement_inside + legend_placement_outside, only_for="linechart_native"),

        #TODO legend labels
        # case("legend_prefer_result_titles", "false", props={"legend_automatic":"true"}),
        # case("legend_prefer_module_display_paths", "false", props={"legend_automatic":"true"}),
        # case("legend_format", "$name in $module", props={"legend_automatic":"false"}),
        # case("legend_replacements", "/ /_/\n/:/!/"),

        # lines
        case("drawstyle", ["auto", "none", "linear", "steps-pre", "steps-mid", "steps-post"]),
        case("linecolor", ["", "green", "#808080"]),
        case("linestyle", ["none", "solid", "dotted", "dashed", "dashdot"]),
        case("linewidth", ["0", "0.5", "1", "5"]),

        # markers
        case("marker", ["auto", "none", ". (dot)", *list(".,^v")]),  # more: ".,v^<>1234|_8osp*xDd"
        case("markersize", ["3","10"], props={"marker":"."}),

        # misc
        case("plt.style", ["default", "ggplot", "grayscale", "seaborn"], only_for=["linechart_mpl", "linechart_separate_mpl"]),
        case("cycle_seed", ["0", "1"], None)

    ]
)

charts += make_charts(
    ["histogramchart_native", "histogramchart_mpl"],
    "all",
    {
        "filter": "runattr:experiment =~ PureAlohaExperiment AND type =~ histogram AND itervar:numHosts =~ 15 AND (itervar:iaMean =~ 1 OR itervar:iaMean =~ 2)",
        "drawstyle": "Outline",
    },
    [
        case(None, None),

        # axes
        case("xaxis_title", "Manual X Axis Title"),
        case("yaxis_title", "Manual Y Axis Title"),
        case("xaxis_min", "5"),
        case("xaxis_max", "10"),
        case("yaxis_min", "1000"),
        case("yaxis_max", "2000"),
        case("yaxis_log", "true"),

        # grid
        case("grid_show", "false"),
        case("grid_density", ["Major", "All"]),

        # legend
        case("legend_show", "false"),
        case("legend_placement", legend_placement_inside, only_for=["linechart_mpl", "linechart_separate_mpl"]),
        case("legend_placement", legend_placement_inside + legend_placement_outside, only_for="linechart_native"),

        # legend labels
        case("legend_prefer_result_titles", "false", props={"legend_automatic":"true"}),
        case("legend_prefer_module_display_paths", "false", props={"legend_automatic":"true"}),
        case("legend_format", "$name in $module", props={"legend_automatic":"false"}),
        case("legend_replacements", "/ /_/\n/:/->/\n/=/==/", props={"legend_automatic":"true"}),
        case("legend_replacements", "/ /_/\n/:/->/\n/=/==/", props={"legend_automatic":"false", "legend_format":"$name in $module"}),

        # histogram
        case("drawstyle", ["Solid", "Outline"]),
        # case("linewidth", ["0", "0.5", "1", "5"]), # TODO
        # case("color", ["", "green", "#808080"]), # TODO
        # case("baseline", ["-1000", "0", "1000"]),  # TODO - doesn't work
        # case("density", ["true", "false"]), # TODO
        case("cumulative", ["false", "true"], props={"normalize":"false"}),
        case("cumulative", ["false", "true"], props={"normalize":"true"}),
        case("show_overflows", ["false", "true"]),

        # misc
        case("plt.style", ["default", "ggplot", "grayscale", "seaborn"], only_for=["linechart_mpl", "linechart_separate_mpl"]),
        case("cycle_seed", ["0", "1"], None)


    #     matplotlibrc.figure.facecolor = ''
    #     matplotlibrc.axes.facecolor = ''
    #     matplotlibrc.legend.frameon = 'true'
    #     matplotlibrc.legend.fancybox = 'false'
    #     matplotlibrc.legend.shadow = 'false'
    #     matplotlibrc = ''
    #     image_export_filename = ''
    #     image_export_width = '6'
    #     image_export_height = '4'
    #     data_export_filename = ''
    ]
)

charts += make_charts(
    ["histogramchart_vectors_native", "histogramchart_vectors_mpl"],
    "all",
    {
        "filter": "runattr:experiment =~ TandemQueueExperiment AND name =~ queueingTime:vector AND runattr:replication =~ #0",
        "drawstyle": "Outline",
    },
    [
        case(None, None),

        # axes
        case("xaxis_title", "Manual X Axis Title"),
        case("yaxis_title", "Manual Y Axis Title"),
        case("xaxis_min", "5"),
        case("xaxis_max", "10"),
        case("yaxis_min", "10"),
        case("yaxis_max", "20"),
        case("yaxis_log", "true"),

        # grid
        case("grid_show", "false"),
        case("grid_density", ["Major", "All"]),

        # legend
        case("legend_show", "false"),
        case("legend_placement", legend_placement_inside, only_for=["linechart_mpl", "linechart_separate_mpl"]),
        case("legend_placement", legend_placement_inside + legend_placement_outside, only_for="linechart_native"),

        # legend labels
        case("legend_prefer_result_titles", "false", props={"legend_automatic":"true"}),
        case("legend_prefer_module_display_paths", "false", props={"legend_automatic":"true"}),
        case("legend_format", "$name in $module", props={"legend_automatic":"false"}),
        case("legend_replacements", "/ /_/\n/:/->/\n/=/==/", props={"legend_automatic":"true"}),
        case("legend_replacements", "/ /_/\n/:/->/\n/=/==/", props={"legend_automatic":"false", "legend_format":"$name in $module"}),

        # histogram
        case("drawstyle", ["Solid", "Outline"]),
        # case("linewidth", ["0", "0.5", "1", "5"]), # TODO
        # case("color", ["", "green", "#808080"]), # TODO
        # case("baseline", ["-10", "0", "10"]), # TODO - doesn't work
        # case("density", ["true", "false"]), # TODO
        case("cumulative", ["false", "true"], props={"normalize":"false"}),
        case("cumulative", ["false", "true"], props={"normalize":"true"}),
        case("show_overflows", ["false", "true"]),

        # misc
        case("plt.style", ["default", "ggplot", "grayscale", "seaborn"], only_for=["linechart_mpl", "linechart_separate_mpl"]),
        case("cycle_seed", ["0", "1"], None)
    ]
)

charts += make_charts(
    ["generic_mpl"],
    "all",
    {
    },
    [
        case("input", "Hello"),
        case("input", ""),
    ]
)

charts += make_charts(
    ["generic_xyplot_native", "generic_xyplot_mpl"],
    "all",
    {
    },
    [
        case(None),
    ]
)

charts += make_charts(
    ["3dchart_itervars_mpl"],
    "all",
    {
        "filter": "runattr:experiment =~ PureAlohaExperiment AND name =~ channelUtilization:last",
        "xaxis_itervar": "iaMean",
        "yaxis_itervar": "numHosts",
        "colormap": "viridis",
        "colormap_reverse": "false",
        "chart_type": "bar"
    },
    [
        case(None, None),
        case("filter", "runattr:experiment =~ PureAlohaExperiment AND type =~ scalar", errmsg="scalars must share the same name"),
        case("filter", "runattr:experiment =~ PureAlohaExperiment AND name =~ channel*"),

        case("xaxis_itervar", "iaMean"),
        case("xaxis_itervar", "numHosts", errmsg="The itervar for the X and Y axes are the same"),
        case("xaxis_itervar", "aa bb", errmsg="iteration variable for the X axis could not be found"),
        case("xaxis_itervar", "", errmsg="set both the X Axis and Y Axis options"),

        case("yaxis_itervar", "iaMean", errmsg="The itervar for the X and Y axes are the same"),
        case("yaxis_itervar", "numHosts"),
        case("yaxis_itervar", "aa bb", errmsg="iteration variable for the Y axis could not be found"),
        case("yaxis_itervar", "", errmsg="set both the X Axis and Y Axis options"),

        case("chart_type", ["points", "surface", "trisurf"]),
    ]
)

charts += make_charts(
    ["boxwhiskers"],
    "all",
    {
        "filter": "runattr:experiment =~ PureAlohaExperiment AND itervar:numHosts =~ 15 AND (itervar:iaMean =~ 1 OR itervar:iaMean =~ 2)",
    },
    [
        case(None, None),


        # axes
        case("xaxis_title", "Manual X Axis Title"),
        case("yaxis_title", "Manual Y Axis Title"),
        # case("xaxis_min", "5"), # TODO: remove
        # case("xaxis_max", "10"), # TODO: remove
        case("yaxis_min", "10"),
        case("yaxis_max", "20"),
        # case("yaxis_log", "true"), # TODO: remove

        # grid
        case("grid_show", "false"),
        case("grid_density", ["Major", "All"]),

        # legend
        case("legend_show", "false"),
        case("legend_placement", legend_placement_inside, only_for=["linechart_mpl", "linechart_separate_mpl"]),
        case("legend_placement", legend_placement_inside + legend_placement_outside, only_for="linechart_native"),

        # misc
        case("plt.style", ["default", "ggplot", "grayscale", "seaborn"], only_for=["linechart_mpl", "linechart_separate_mpl"]),
        case("cycle_seed", ["0", "1"], None)
    ]
)

# generate analysis file
inputs = [ "/resultfiles/aloha", "/resultfiles/fifo", "/resultfiles/tandemfifos" ]
analysis = Analysis(inputs=inputs, items=charts)
analysis.to_anf_file("all_the_tests.anf")

# print which chart templates are not covered here
tested = set([chart.template for chart in charts])
all = set(templates.keys())
untested = all.difference(tested)
print("Untested chart templates (not covered by this test):", untested)

# run the tests
# wd = os.path.abspath(".")
# workspace = Workspace('../../../samples/')
# for chart in charts:
#     analysis.export_image(chart, wd, workspace, format='png', target_folder='export')

