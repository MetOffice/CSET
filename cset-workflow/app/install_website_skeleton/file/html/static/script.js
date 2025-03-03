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

function construct_sidebar_from_data(data) {
  const sidebar = document.getElementById("plot-selector");
  // Button icons.
  const icons = { left: "◧", full: "▣", right: "◨" };

  for (const category in data) {
    // Details element for category.
    const details = document.createElement("details");

    // Title for category and case_date (summary element).
    const summary = document.createElement("summary");
    summary.textContent = `${category}`;
    details.append(summary);

    for (const case_date in data[category]) {
      // Submenu for case_date.
      const subcategory = document.createElement("details");


      // Title for case_date.
      const subcategory_header = document.createElement("summary");
      subcategory_header.textContent = `${case_date}`;
      subcategory.append(subcategory_header);


      // Menu of plots for this category and case_date.
      const category_menu = document.createElement("menu");

      // Add each plot.
      for (const plot in data[category][case_date]) {
        // Menu entry for plot.
        const list_item = document.createElement("li");
        list_item.textContent = data[category][case_date][plot];

        // Container element for plot position chooser buttons.
        const position_chooser = document.createElement("div");
        position_chooser.classList.add("plot-position-chooser");

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
            document.getElementById(`plot-frame-${position}`).src = `plots/${plot}`;
          });

          // Add button to chooser.
          position_chooser.append(button);
        }

        // Add position chooser to entry.
        list_item.append(position_chooser);

        // Add entry to the menu.
        category_menu.append(list_item);
      }
      subcategory.append(category_menu);
      details.append(subcategory);
    }
    // Add details to the document (e.g., a specific container element).
    sidebar.append(details);

  }
}

// Plot selection sidebar
function setup_plots_sidebar() {
  // Skip if there is no sidebar on page.
  if (!document.getElementById("plot-selector")) {
    return;
  }
  // Loading of plot index file, and adding them to the sidebar.
  fetch("plots/index.json")
    .then((response) => {
      // Display a message and stop if the fetch fails.
      if (!response.ok) {
        const message = `There was a problem fetching the index. Status Code: ${response.status}`;
        console.warn(message);
        window.alert(message);
        return;
      }
      response.json().then(construct_sidebar_from_data);
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

// Run everything.
setup_description_toggle_button();
setup_clear_view_button();
setup_plots_sidebar();
