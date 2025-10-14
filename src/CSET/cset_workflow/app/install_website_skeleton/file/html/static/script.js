// JavaScript code that is used by the pages. Plots should not rely on this
// file, as it will not be stable.

// Toggle display of the extended description for plots. Global variable so it
// can be referenced at plot insertion time.
let description_shown = true;

function enforce_description_toggle() {
  const description_toggle_button = document.getElementById("description-toggle");
  if (description_shown) {
    description_toggle_button.textContent = "⇲ Hide description";
  } else {
    description_toggle_button.textContent = "⇱ Show description";
  }
  label: for (plot_frame of document.querySelectorAll("iframe")) {
    const description_container = plot_frame.contentDocument.getElementById(
      "description-container"
    );
    // Skip doing anything if plot not loaded.
    if (!description_container) {
      continue label;
    }
    // Hide the description if it is exists and is shown, and show if hidden.
    // Explicitly add and remove rather than toggle class to prevent the plots
    // getting out of sync.
    if (description_shown) {
      description_container.classList.remove("hidden");
    } else {
      description_container.classList.add("hidden");
    }
  }
}

// Hook up button.
function setup_description_toggle_button() {
  const description_toggle_button = document.getElementById("description-toggle");
  // Skip if there is no description toggle on page.
  if (!description_toggle_button) {
    return;
  }
  description_toggle_button.addEventListener("click", () => {
    description_shown = !description_shown;
    enforce_description_toggle();
  });
  // Ensure the description toggle persists across changing the frame content.
  for (const plot_frame of document.querySelectorAll("iframe")) {
    plot_frame.addEventListener("load", () => {
      enforce_description_toggle();
    });
  }
}

// Display a single plot frame on the page.
function ensure_single_frame() {
  const single_frame = document.getElementById("single-frame");
  const dual_frame = document.getElementById("dual-frame");
  dual_frame.classList.add("hidden");
  single_frame.classList.remove("hidden");
}

// Display two side-by-side plot frames on the page.
function ensure_dual_frame() {
  const single_frame = document.getElementById("single-frame");
  const dual_frame = document.getElementById("dual-frame");
  single_frame.classList.add("hidden");
  dual_frame.classList.remove("hidden");
}

function add_to_sidebar(record, facet_values) {
  const diagnostics_list = document.getElementById("diagnostics");

  // Add entry's display name.
  const entry_title = document.createElement("h2");
  entry_title.textContent = record["title"];

  const facets = document.createElement("ul");
  for (const facet in record) {
    if (facet != "title" && facet != "path") {
      // Create card for diagnostic.
      const li = document.createElement("li");
      li.textContent = `${facet}: ${record[facet]}`;
      facets.append(li);
      // Record facet values.
      if (!(facet in facet_values)) {
        facet_values[facet] = new Set();
      }
      const values = facet_values[facet];
      values.add(record[facet]);
    }
  }

  // Container element for plot position chooser buttons.
  const position_chooser = document.createElement("div");
  position_chooser.classList.add("plot-position-chooser");

  // Bind path to name in this scope to ensure it sticks around for callbacks.
  const path = record["path"];
  // Button icons.
  const icons = { left: "◧", full: "▣", right: "◨", popup: "↗" };

  // Add buttons for each position.
  for (const position of ["left", "full", "right", "popup"]) {
    // Create button.
    const button = document.createElement("button");
    button.classList.add(position);
    button.textContent = icons[position];

    // Add a callback updating the iframe when the link is clicked.
    button.addEventListener("click", (event) => {
      event.preventDefault();
      // Open new window for popup.
      if (position == "popup") {
        window.open(`plots/${path}`, "_blank", "popup,width=800,height=600");
        return;
      }
      // Set the appropriate frame layout.
      position == "full" ? ensure_single_frame() : ensure_dual_frame();
      document.getElementById(`plot-frame-${position}`).src = `plots/${path}`;
    });

    // Add button to chooser.
    position_chooser.append(button);
  }

  // Create entry.
  const entry = document.createElement("li");

  // Add name, facets, and position chooser to entry.
  entry.append(entry_title, facets, position_chooser);

  // Join entry to the DOM.
  diagnostics_list.append(entry);
}

function add_facet_dropdowns(facet_values) {
  const fieldset = document.getElementById("filter-facets");

  for (const facet in facet_values) {
    const label = document.createElement("label");
    label.setAttribute("for", `facet-${facet}`);
    label.textContent = facet;
    const select = document.createElement("select");
    select.id = `facet-${facet}`;
    select.name = facet;
    const null_option = document.createElement("option");
    null_option.value = "";
    null_option.defaultSelected = true;
    null_option.textContent = "--- Any ---";
    select.append(null_option);
    // Sort facet values.
    const values = Array.from(facet_values[facet]);
    values.sort();
    for (const value of values) {
      const option = document.createElement("option");
      option.textContent = value;
      select.append(option);
    }
    select.addEventListener("change", updateFacetQuery);

    // Add to DOM.
    fieldset.append(label, select);
  }
}

// Update query based on facet dropdown value.
function updateFacetQuery(e) {
  const facet = e.target.name;
  const value = e.target.value;
  const queryElem = document.getElementById("filter-query");
  const query = queryElem.value;
  let new_query;
  // Construct regular expression matching facet condition.
  const pattern = RegExp(`${facet}:\\s*('[^']*'|"[^"]*"|[^ \\t\\(\\)]+)`, "i");
  if (value == "" && query.match(pattern)) {
    // Facet unselected, remove from query.
    new_query = query.replace(pattern, "");
  } else if (query.match(pattern)) {
    // Facet value selected, update the query.
    new_query = query.replace(pattern, `${facet}:"${value}"`);
  } else {
    // Facet value selected, add the query.
    new_query = query + ` ${facet}:"${value}"`;
  }
  queryElem.value = new_query.trim();
  doSearch();
}

// Plot selection sidebar.
function setup_plots_sidebar() {
  // Skip if there is no sidebar on page.
  if (!document.getElementById("plot-selector")) {
    return;
  }
  // Loading of plot index file, and adding them to the sidebar.
  fetch("plots/facets.jsonl")
    .then((response) => {
      // Display a message and stop if the fetch fails.
      if (!response.ok) {
        const message = `There was a problem fetching the index. Status Code: ${response.status}`;
        console.warn(message);
        window.alert(message);
        return;
      }
      response.text().then((data) => {
        const facet_values = {};
        // Remove throbber now download has finished.
        document.querySelector("#diagnostics > loading-throbber").remove();
        for (let line of data.split("\n")) {
          line = line.trim();
          // Skip blank lines.
          if (line.length) {
            add_to_sidebar(JSON.parse(line), facet_values);
          }
        }
        add_facet_dropdowns(facet_values);
        // Do search if we already have a query specified in the URL.
        const search = document.getElementById("filter-query");
        const params = new URLSearchParams(document.location.search);
        const initial_query = params.get("q");
        if (initial_query) {
          search.value = initial_query;
          doSearch();
        }
      });
    })
    .catch((err) => {
      // Catch non-HTTP fetch errors.
      console.error("Plot index could not be retrieved: ", err);
    });
}

function setup_clear_view_button() {
  // Reset frames to placeholder view.
  function clear_frames() {
    for (plot_frame of document.querySelectorAll("iframe")) {
      plot_frame.src = "placeholder.html";
    }
    ensure_single_frame();
  }

  const clear_view_button = document.getElementById("clear-plots");
  clear_view_button.addEventListener("click", clear_frames);
}

function setup_clear_search_button() {
  const clear_search_button = document.getElementById("clear-query");
  clear_search_button.addEventListener("click", () => {
    document.getElementById("filter-query").value = "";
    doSearch();
  });
}

// Parse the query, returning a comparison function.
function parse_query(query) {
  // TODO: Port query parser from parser.py
  const title = query.toLowerCase();

  // Returns true or false for a given event based on the query.
  function test(entry) {
    return entry.textContent.includes(title);
  }

  return test;
}

// Filter the displayed diagnostics by the query.
function doSearch() {
  const query = document.getElementById("filter-query").value;
  // Update URL in address bar to match current query, deleting if blank.
  const url = new URL(document.location.href);
  query ? url.searchParams.set("q", query) : url.searchParams.delete("q");
  // Updates the URL without reloading the page.
  history.pushState(history.state, "", url.href);

  console.log("Search query:", query);
  const test = parse_query(query);

  // Filter all entries.
  for (const entry of document.querySelectorAll("#diagnostics > li")) {
    // Show entries matching filter and hide entries that don't.
    if (test(entry)) {
      entry.classList.remove("hidden");
    } else {
      entry.classList.add("hidden");
    }
  }
}

// For performance don't search on every keystroke immediately. Instead wait
// until quarter of a second of no typing has elapsed. To maximised perceived
// responsiveness immediately perform the search if a space is typed, as that
// indicates a completed search term.
let searchTimeoutID = undefined;
function debounce(e) {
  clearTimeout(searchTimeoutID);
  if (e.data == " ") {
    doSearch();
  } else {
    searchTimeoutID = setTimeout(doSearch, 250);
  }
}

// Diagnostic filtering searchbar.
function setup_search() {
  const search = document.getElementById("filter-query");
  search.addEventListener("input", debounce);
  // Immediately search if input is unfocused.
  search.addEventListener("change", doSearch);
}

// Run everything.
setup_description_toggle_button();
setup_clear_view_button();
setup_clear_search_button();
setup_plots_sidebar();
setup_search();
