const width = 640,
      height = 480,
      margin = 30;

// Create SVG container and a gray background.
const svg = d3.select("#figure").append("svg")
    .attr("width", width)
    .attr("height", height);

svg.append("g")
    .append("rect")
    .attr("class", "background")
    .attr("width", width)
    .attr("height", height)
    .attr("fill", "rgb(245,245,245)");

// Create the horizontal (x) / vertical (y) scales--we've prescaled the features
// to live 0-1.
const xscale = d3.scaleLinear()
    .domain([0, 1]).nice()
    .range([margin, width - margin])
    .unknown(margin);

const yscale = d3.scaleLinear()
    .domain([0, 1]).nice()
    .range([height - margin, margin])
    .unknown(height - margin);

// Append the axes.
svg.append("g")
    .attr("transform", `translate(0,${height - margin})`)
    .call(d3.axisBottom(xscale))
    .call(g => g.select(".domain").remove())
    .call(g => g.selectAll("text").remove());

svg.append("g")
    .attr("transform", `translate(${margin},0)`)
    .call(d3.axisLeft(yscale))
    .call(g => g.select(".domain").remove())
    .call(g => g.selectAll("text").remove());

// Add a grid.
svg.append("g")
    .attr("stroke", "rgb(215, 215, 215)")
    .attr("stroke-opacity", 0.7)
    .call(g => g.append("g")
        .selectAll("line")
        .data(xscale.ticks())
        .join("line")
            .attr("x1", d => 0.5 + xscale(d))
            .attr("x2", d => 0.5 + xscale(d))
            .attr("y1", margin)
            .attr("y2", height - margin))
    .call(g => g.append("g")
        .selectAll("line")
        .data(yscale.ticks())
        .join("line")
            .attr("y1", d => 0.5 + yscale(d))
            .attr("y2", d => 0.5 + yscale(d))
            .attr("x1", margin)
            .attr("x2", width - margin));

// Create a tooltip.
const tooltip = d3.select("body").append("div")
    .attr("class", "bg-secondary-subtle")
    .attr("id", "tooltip")
    .attr("style", "position: absolute; opacity: 0;");

function tooltipMouseOver(e, d) {
    tooltip
        .style("opacity", 1)
        .text(`${d['year']}-${d['author']}`);
}

function tooltipMouseOut() {
    tooltip.style("opacity", 0);
}

function tooltipMouseMove(e) {
    tooltip
        .style("left", (e.pageX + 10) + "px")
        .style("top", (e.pageY + 10) + "px");
}

// Plot the data...
d3.csv("placeholder.csv").then(function(data) {
    // Get colors for all years.
    years = data.map(d => d["year"]);
    const coloryear = d3.scaleSequential(
        [Math.min(...years), Math.max(...years)],
        d3.interpolateViridis);

    // Get colors for unique authors.
    authors = Array.from(new Set(data.map(d => d["author"])));
    const rand = d3.randomUniform(0, 1);
    const colorauth = authors.reduce((ret, a) => ({...ret, [a]: d3.interpolateSpectral(rand())}), {});

    const dot = svg.append("g");

    function drawEmbeddings() {
        const emb_key = (() => {
            switch (d3.select("input[name='embradio']:checked").node().id) {
                case "tfidf":
                    return "tfidf";
                case "ada002":
                    return "openai_ada_002";
                case "3small":
                    return "openai_3_small";
            }
        })();

        const dim_key = (() => {
            switch (d3.select("input[name='dimradio']:checked").node().id) {
                case "pca":
                    return "pca";
                case "tsne":
                    return "tsne";
            }
        })();

        const color = ((d) => {
            switch (d3.select("input[name='colradio']:checked").node().id) {
                case "year":
                    return coloryear(d["year"]);
                case "auth":
                    return colorauth[d["author"]];
            }
        });

        dot.selectAll("circle")
            .data(data)
            .join("circle")
                .attr("fill", color)
                .attr("opacity", 0.7)
                .attr("r", 6)
                .on("mouseover", tooltipMouseOver)
                .on("mouseout", tooltipMouseOut)
                .on("mousemove", tooltipMouseMove)
                .transition()
                .duration(500)
                .attr("transform", d => {
                    xvals = d[`x_${dim_key}_${emb_key}`];
                    yvals = d[`y_${dim_key}_${emb_key}`];
                    return `translate(${xscale(xvals)},${yscale(yvals)})`;
                });
    }

    // Initial draw.
    drawEmbeddings();

    // Hook up draw to change events on inputs.
    d3.select("#embedding-select").on("change", () => drawEmbeddings());
    d3.select("#dimension-select").on("change", () => drawEmbeddings());
    d3.select("#color-select").on("change", () => drawEmbeddings());
});
