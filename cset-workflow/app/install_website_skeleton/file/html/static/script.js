// JavaScript code that is used by the pages. Plots should not rely on this
// file, as it will not be stable.

// Display workflow status on index page.
function update_workflow_status() {
  const workflow_status = document.getElementById("workflow_status");
  // Skip if there is no workflow status on page.
  if (!workflow_status) {
    return;
  }
  fetch("status.json")
    .then((response) => {
      if (!response.ok) {
        const message = `There was a problem fetching the index. Status Code: ${response.status}`;
        console.warn(message);
        window.alert(message);
        return;
      }
      response.json().then((data) => {
        if (window.Sanitizer) {
          // Sanitizer API is supported
          workflow_status.setHTML(data.status);
        } else {
          // Fallback where it isn't
          workflow_status.innerHTML = data.status;
        }
      });
    })
    .catch((err) => {
      // Catch non-HTTP fetch errors.
      console.error("Workflow status could not be retrieved: ", err);
    });
}

// Toggle display of the extended description for plots.
function setup_description_toggle_button() {
  const description_toggle_button = document.getElementById("description-toggle");
  // Skip if there is no description on page.
  if (!description_toggle_button) {
    return;
  }
  let description_shown = true;

  function toggle_description() {
    const description_container_1 = document
      .getElementById("plot_frame_1")
      .contentDocument.getElementById("description-container");

    // Ensure second frame exists before trying to use it.
    let description_container_2 = null;
    if (document.getElementById("plot_frame_2")) {
      description_container_2 = document
        .getElementById("plot_frame_2")
        .contentDocument.getElementById("description-container");
    }

    // Hide the description if it is exists and is shown, and show if hidden.
    // Explicitly add and remove rather than toggle class to prevent the two
    // plots getting out of sync.
    if (description_shown) {
      description_shown = false;
      description_toggle_button.textContent = "⇱ Toggle Description";
      if (description_container_1) {
        description_container_1.classList.add("hidden");
      }
      if (description_container_2) {
        description_container_2.classList.add("hidden");
      }
    } else {
      description_shown = true;
      description_toggle_button.textContent = "⇲ Toggle Description";
      if (description_container_1) {
        description_container_1.classList.remove("hidden");
      }
      if (description_container_2) {
        description_container_2.classList.remove("hidden");
      }
    }
  }

  description_toggle_button.addEventListener("click", toggle_description);
}

// Plot selection dropdown menus.
function setup_plots_dropdown() {
  const dropdown_background = document.querySelectorAll(".dropdown > .background");
  // Skip if there is no dropdown on page.
  if (!dropdown_background) {
    return;
  }

  // Closing of dropdown.
  function close_dropdowns(event) {
    if (event instanceof KeyboardEvent) {
      if (event.key != "Escape") {
        return;
      }
    }
    for (const elem of document.querySelectorAll(".dropdown")) {
      elem.removeAttribute("open");
    }
  }

  // Register event listeners.
  for (const elem of dropdown_background) {
    elem.addEventListener("click", close_dropdowns);
  }
  document.addEventListener("keydown", close_dropdowns);
  for (const elem of document.querySelectorAll(".dropdown-close")) {
    elem.addEventListener("click", close_dropdowns);
  }

  // Loading of plot index file, and adding them to dropdown.
  fetch("plots/index.json")
    .then((response) => {
      // Display a message and stop if the fetch fails.
      if (!response.ok) {
        const message = `There was a problem fetching the index. Status Code: ${response.status}`;
        console.warn(message);
        window.alert(message);
        return;
      }
      response.json().then((data) => {
        // Number of the dropdown within the page.
        let dropdown_number = 1;
        // Loop through all the dropdowns and populate them.
        const dropdowns = document.querySelectorAll(
          ".dropdown > .dropdown-content > .tabset > .tab-panels"
        );
        for (const dropdown_tab_content of dropdowns) {
          // Number of the tab within the dropdown.
          let tab_number = 0;
          for (model in data) {
            // Control for tab.
            const input_element = document.createElement("input");
            input_element.type = "radio";
            input_element.name = `tabset_${dropdown_number}`;
            input_element.id = `tab_${dropdown_number}_${tab_number}`;
            input_element.ariaControls = `panel_${dropdown_number}_${tab_number}`;
            dropdown_tab_content.insertAdjacentElement("beforebegin", input_element);

            // Label for tab
            const label_element = document.createElement("label");
            label_element.htmlFor = `tab_${dropdown_number}_${tab_number}`;
            label_element.textContent = model;
            dropdown_tab_content.insertAdjacentElement("beforebegin", label_element);

            // Tab panel with links to plots
            const tab_section = document.createElement("section");
            tab_section.id = `panel_${dropdown_number}_${tab_number}`;
            tab_section.className = "tab-panel";

            // Menu of links.
            const tab_section_menu = document.createElement("menu");
            tab_section_menu.className = "plot-selector";
            // Populate with links.
            for (plot in data[model]) {
              // Create a link to the plot.
              const link = document.createElement("a");
              link.href = `plots/${data[model][plot]}`;
              link.textContent = plot;
              // Add a callback updating the iframe when the link is clicked.
              const frame_id = `plot_frame_${dropdown_number}`;
              link.addEventListener("click", (event) => {
                event.preventDefault();
                document.getElementById(frame_id).src = link.href;
              });
              // Add the link to the menu (a list).
              const list_item = document.createElement("li");
              list_item.append(link);
              tab_section_menu.append(list_item);
            }
            // Join everything to the DOM.
            tab_section.append(tab_section_menu);
            dropdown_tab_content.append(tab_section);

            // On to the next tab.
            tab_number++;
          }
          // Select first tab.
          dropdown_tab_content.parentNode.querySelector("input").checked = true;

          // On to the next dropdown.
          dropdown_number++;
        }
      });
    })
    .catch((err) => {
      // Catch non-HTTP fetch errors.
      console.error("Plot index could not be retrieved: ", err);
    });
}

// Actually run everything.
update_workflow_status();
setup_description_toggle_button();
setup_plots_dropdown();
