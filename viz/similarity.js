{ // limit scope...
d3.json("presidential_2.json").then(function(data) {
    const button = document.getElementById("similarity-button");
    const button_text = document.createTextNode("");
    button.appendChild(button_text);

    const nearest = [
        "tfidf",
        "openai-ada-002",
        "openai-3-small"
    ].map(d => ({
        "data_key": d,
        "element": document.getElementById(`nearest-${d}`)
    }));

    let buttons = {};
    let active_key = 0;

    function setActive(key) {
        // Update selector button text and set active.
        const val = `${data[key][0]["author"]}-${data[key][0]["year"]}`;
        button_text.nodeValue = val;

        buttons[active_key].classList.remove("active");
        buttons[key].classList.add("active");
        active_key = key;

        // Update lists.
        nearest.forEach(l => {
            // Clear list.
            while(l["element"].lastChild) {
                l["element"].removeChild(l["element"].lastChild);
            }

            // Start at index 1, since index 0 is the same document...
            data[key].slice(1, 11).map(d => {
                let entry = document.createElement("li");
                entry.classList.add("list-group-item");
                entry.classList.add("align-items-start");
                l["element"].appendChild(entry);

                distance = d[`${l["data_key"]}_distance`];
                author = d[`${l["data_key"]}_author`];
                year = d[`${l["data_key"]}_year`];
                let content = document.createTextNode(
                    `(${distance.toFixed(3)}) ${author}-${year}`
                );
                entry.appendChild(content);
            });
        });
    }

    function selectHandler(e) {
        setActive(this.getAttribute("key"));
    }

    // Populate dropdown menu.
    const selector_list = document.getElementById("similarity-selector-list");
    for (let key in data) {
        let address = document.createElement("li");
        selector_list.appendChild(address)

        let button = document.createElement("button");
        button.classList.add("dropdown-item");
        button.setAttribute("key", key);
        address.appendChild(button);

        const val = `${data[key][0]["author"]}-${data[key][0]["year"]}`;
        let content = document.createTextNode(val);
        button.appendChild(content);
        button.addEventListener("click", selectHandler, key);

        buttons[key] = button;
    };

    // Set the first key active.
    setActive(0);
});
/*
const width = 720,
      height = 720,
      margin = 30;

// Create SVG container and a gray background.
const svg = d3.select("#similarity").append("svg")
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", [0, 0, width, height])
    .attr("style", "max-width: 100%; height: auto;");

svg.append("g")
    .append("rect")
    .attr("class", "background")
    .attr("width", width)
    .attr("height", height)
    .attr("fill", "rgb(245,245,245)");

d3.json("presidential_2.json").then(function(data) {
    const addresses = data["addresses"];
    const num_addresses = addresses.length;

    const key = "tfidf";
    // const key = "openai-ada-002";
    // const key = "openai-3-small";
    const dist_max = Math.max(...data["condensed_distance"][key]);
    const cscale = d3.scaleSequential(
        [0, dist_max],
        d3.interpolateRgb("black", "white")
    );

    const color = (d) => {
        const coords = [
            Math.floor(d / num_addresses),
            d % num_addresses
        ];
        const i = Math.min(...coords);
        const j = Math.max(...coords);
        let val = 0.0;
        if (i != j) {
            const index = num_addresses * i + j - ((i + 2) * (i + 1)) / 2;
            val = data["condensed_distance"][key][index];
        }

        return cscale(val);
    };

    const dscale = d3.scaleBand(d3.range(num_addresses), [0, width]);

    svg.append("g")
        .selectAll()
        .data(d3.range(num_addresses * num_addresses))
            .join("rect")
                .attr("width", dscale.bandwidth() - 1)
                .attr("height", dscale.bandwidth() - 1)
                .attr("x", d => dscale(d % num_addresses))
                .attr("y", d => dscale(Math.floor(d / num_addresses)))
                .attr("fill", d => color(d));
});
*/
}
