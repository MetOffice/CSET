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

function add_to_sidebar(record) {
  const diagnostics_list = document.getElementById("diagnostics");

  // Add entry's display name.
  const entry_name = document.createElement("h3")
  entry_name.textContent = record["name"];

  const facets = document.createElement("dl");
  for (const facet in record) {
    const dt = document.createElement("dt");
    dt.textContent = facet;
    const dd = document.createElement("dd");
    dd.textContent = record[facet];
    facets.append(dt, dd);
  }


  // Container element for plot position chooser buttons.
  const position_chooser = document.createElement("div");
  position_chooser.classList.add("plot-position-chooser");

  // Bind path to name in this scope to ensure it sticks around for callbacks.
  const path = record["path"];
  // Button icons.
  const icons = { left: "◧", full: "▣", right: "◨" };

  // Add buttons for each position.
  for (const position of ["left", "full", "right"]) {
    // Create button.
    const button = document.createElement("button");
    button.classList.add(position);
    button.textContent = icons[position];

    // Add a callback updating the iframe when the link is clicked.
    button.addEventListener("click", (event) => {
      event.preventDefault();
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
  entry.append(entry_name, facets, position_chooser);

  // Join entry to the DOM.
  diagnostics_list.append(entry);
}


// Plot selection sidebar
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
        for (let line of data.split("\n")) {
          line = line.trim();
          // Skip blank lines.
          if (line.length) {
            add_to_sidebar(JSON.parse(line));
          }
        }
        // Do search if we already have a query specified in the URL.
        const search = document.getElementById("filter-query");
        const params = new URLSearchParams(document.location.search);
        const initial_query = params.get("q");
        if (initial_query) {
          search.value = initial_query;
          doSearch();
        }
      })
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

// Parse the query, returning a comparison function.
function parse_query(query) {
  // TODO: Parse the query into an easily compared form.
  const title = query.toLowerCase()

  // Returns true or false for a given event based on the query.
  function test(entry) {
    // TODO: Implement comparison of facets.
    return entry.textContent.includes(title)
  }

  return test
}

// Filter the displayed diagnostics by the query.
function doSearch() {
  const query = document.getElementById("filter-query").value;
  // Update URL in address bar to match current query.
  const url = new URL(document.location.href);
  url.searchParams.set("q", query)
  // Updates the URL without reloading the page.
  history.pushState(history.state, "", url.href)

  console.log("Search query:", query);
  const test = parse_query(query)

  // Filter all entries.
  for (const entry of document.querySelectorAll("#diagnostics > li")) {
    // Show entries matching filter and hide entries that don't.
    if (test(entry)) {
      entry.classList.remove("hidden")
    } else {
      entry.classList.add("hidden")
    }
  }
}

// For performance don't search on every keystroke immediately. Instead wait
// until half a second of no typing has elapsed. To maximised perceived
// responsiveness immediately perform the search if a space is typed, as that
// indicates a completed search term.
let searchTimeoutID = undefined;
function debounce(e) {
  clearTimeout(searchTimeoutID);
  if (e.data == " ") {
    doSearch();
  } else {
    searchTimeoutID = setTimeout(doSearch, 500);
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
setup_plots_sidebar();
setup_search();
