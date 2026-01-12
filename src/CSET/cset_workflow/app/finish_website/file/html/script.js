// JavaScript code that is used by the pages. Plots should not rely on this
// file, as it will not be stable.

/** Search query lexer and parser.
 *
 * EBNF for filter.
 *
 * query = expression ;
 *
 * expression = condition
 *            | expression , combiner ? , expression
 *            | "NOT" , expression
 *            | "(" , expression , ")" ;
 *
 * combiner = "AND"
 *          | "OR" ;
 *
 * condition = facet ? , operator ? , value ;
 *
 * facet = LITERAL ;
 *
 * value = LITERAL ;
 *
 * operator = IN
 *          | EQUALS ;
 *          | LESS_THAN
 *          | GREATER_THAN
 *          | LESS_THAN_OR_EQUALS
 *          | GREATER_THAN_OR_EQUALS
 */

class Literal {
  constructor(value) {
    this.value = value;
  }
}

const Parenthesis = {
  BEGIN: "BEGIN",
  END: "END",
};

const Operator = {
  IN: "IN",
  EQUALS: "EQUALS",
  LESS_THAN: "LESS_THAN",
  GREATER_THAN: "GREATER_THAN",
  LESS_THAN_OR_EQUALS: "LESS_THAN_OR_EQUALS",
  GREATER_THAN_OR_EQUALS: "GREATER_THAN_OR_EQUALS",
};

const Combiner = {
  NOT: "NOT",
  AND: "AND",
  OR: "OR",
};

const TokenTypes = {
  Literal: Literal,
  Parenthesis: Parenthesis,
  Operator: Operator,
  Combiner: Combiner,
};

const TOKEN_SPEC = {
  Parenthesis_BEGIN: "\\(",
  Parenthesis_END: "\\)",
  Operator_GREATER_THAN_OR_EQUALS: "<=",
  Operator_GREATER_THAN: "<",
  Operator_LESS_THAN_OR_EQUALS: ">=",
  Operator_LESS_THAN: ">",
  Operator_EQUALS: "=",
  Operator_IN: ":",
  Combiner_NOT: "\\bnot\\b",
  Combiner_AND: "\\band\\b",
  Combiner_OR: "\\bor\\b",
  LexOnly_WHITESPACE: "\\s+",
  LexOnly_LITERAL: `'[^']*'|"[^"]*"|[^\\s\\(\\):=<>]+`,
};

const TOKEN_REGEX = RegExp(
  Array.from(
    Object.entries(TOKEN_SPEC).map((pair) => {
      return `(?<${pair[0]}>${pair[1]})`;
    }),
  ).join("|"),
  "ig",
);

// Lex input string into tokens.
function lexer(query) {
  const tokens = [];
  for (const match of query.matchAll(TOKEN_REGEX)) {
    // Split into tokens by matching the capture group names from TOKEN_SPEC.
    if (!match.groups) {
      throw new SyntaxError("Query did not consist of valid tokens.");
    }
    let [kind, value] = Object.entries(match.groups).filter(
      (pair) => pair[1] !== undefined,
    )[0];
    switch (kind) {
      case "LexOnly_WHITESPACE":
        // Skip whitespace.
        continue;
      case "LexOnly_LITERAL":
        // Unquote and store value for literals.
        if (/^".*"$|^'.+'$/.test(value)) {
          value = value.slice(1, -1);
        }
        tokens.push(new Literal(value));
        break;
      default:
        // Tokens for Operators and Combiners.
        const kind_split_position = kind.indexOf("_");
        const kind_type = kind.slice(0, kind_split_position);
        const kind_value = kind.slice(kind_split_position + 1);
        tokens.push(TokenTypes[kind_type][kind_value]);
        break;
    }
  }
  return tokens;
}

class Condition {
  constructor(value, facet, operator) {
    // Allow constructing a Condition from a Condition, e.g: (((Condition)))
    if (typeof value === "function") {
      this.func = value;
      return;
    }
    const v = value.value.toLowerCase();
    const f = facet.value;
    let cond_func;
    switch (operator) {
      case Operator.IN:
        cond_func = function cond_in(d) {
          return f in d && d[f].toLowerCase().includes(v);
        };
        break;
      case Operator.EQUALS:
        cond_func = function cond_eq(d) {
          return f in d && v === d[f].toLowerCase();
        };
        break;
      case Operator.GREATER_THAN:
        cond_func = function cond_gt(d) {
          return f in d && v > d[f].toLowerCase();
        };
        break;
      case Operator.GREATER_THAN_OR_EQUALS:
        cond_func = function cond_gte(d) {
          return f in d && v >= d[f].toLowerCase();
        };
        break;
      case Operator.LESS_THAN:
        cond_func = function cond_lt(d) {
          return f in d && v < d[f].toLowerCase();
        };
        break;
      case Operator.LESS_THAN_OR_EQUALS:
        cond_func = function cond_lte(d) {
          return f in d && v <= d[f].toLowerCase();
        };
        break;
      default:
        throw new Error(`Invalid operator: ${operator}`);
    }
    this.func = cond_func;
  }

  test(d) {
    return this.func(d);
  }

  and(other) {
    return new Condition((d) => this.test(d) && other.test(d));
  }

  or(other) {
    return new Condition((d) => this.test(d) || other.test(d));
  }

  invert() {
    return new Condition((d) => !this.test(d));
  }
}

// Parse a grouped expression from a stream of tokens.
function parse_grouped_expression(tokens) {
  if (tokens.length < 2 || tokens[0] !== Parenthesis.BEGIN) {
    return [0, null];
  }
  let offset = 1;
  let depth = 1;
  while (depth > 0 && offset < tokens.length) {
    switch (tokens[offset]) {
      case Parenthesis.BEGIN:
        depth += 1;
        break;
      case Parenthesis.END:
        depth -= 1;
        break;
    }
    offset += 1;
  }
  if (depth !== 0) {
    throw new Error("Unmatched parenthesis.");
  }
  // Recursively parse the grouped expression.
  inner_expression = parse_expression(tokens.slice(1, offset - 1));
  return [offset, inner_expression];
}

// Parse a condition from a stream of tokens.
function parse_condition(tokens) {
  if (
    tokens[0] instanceof Literal &&
    tokens[1] in Operator &&
    tokens[2] instanceof Literal
  ) {
    // Value to search for in facet with operator.
    return [3, new Condition(tokens[2], (facet = tokens[0]), (operator = tokens[1]))];
  } else if (tokens[0] instanceof Literal) {
    // Just a value to search for.
    return [
      1,
      new Condition(
        tokens[0],
        (facet = new Literal("title")),
        (operator = Operator.IN),
      ),
    ];
  } else {
    // Not matched as a condition.
    return [0, null];
  }
}

// Collapse all NOTs in a list of conditions.
function evaluate_not(conditions) {
  const negated_conditions = [];
  let index = 0;
  while (index < conditions.length) {
    if (conditions[index] === Combiner.NOT && conditions[index + 1] === Combiner.NOT) {
      // Skip double NOTs, as they negate each other.
      index += 2;
    } else if (
      conditions[index] === Combiner.NOT &&
      conditions[index + 1] instanceof Condition
    ) {
      const right = conditions[index + 1];
      negated_conditions.push(right.invert());
      index += 2;
    } else if (conditions[index] !== Combiner.NOT) {
      negated_conditions.push(conditions[index]);
      index += 1;
    } else {
      throw new Error("Unprocessable NOT.");
    }
  }
  return negated_conditions;
}

// Collapse all explicit and implicit ANDs in a list of conditions.
function evaluate_and(conditions) {
  const anded_conditions = [];
  let index = 0;
  while (index < conditions.length) {
    let left = null;
    if (anded_conditions.length) {
      left = anded_conditions.pop();
    }
    if (
      left instanceof Condition &&
      conditions[index] === Combiner.AND &&
      conditions[index + 1] instanceof Condition
    ) {
      const right = conditions[index + 1];
      anded_conditions.push(left.and(right));
      index += 2;
    } else if (left instanceof Condition && conditions[index] instanceof Condition) {
      const right = conditions[index];
      anded_conditions.push(left.and(right));
      index += 2;
    } else if (conditions[index] !== Combiner.AND) {
      if (left !== null) {
        anded_conditions.push(left);
      }
      const right = conditions[index];
      anded_conditions.push(right);
      index += 1;
    } else {
      throw new Error("Unprocessable AND.");
    }
  }
  return anded_conditions;
}

// Collapse all ORs in a list of conditions.
function evaluate_or(conditions) {
  const ored_conditions = [];
  let index = 0;
  while (index < conditions.length) {
    if (
      conditions[index] instanceof Condition &&
      conditions[index + 1] === Combiner.OR &&
      conditions[index + 2]
    ) {
      const left = conditions[index];
      const right = conditions[index + 2];
      ored_conditions.push(left.or(right));
      index += 3;
    } else if (conditions[index] !== Combiner.OR) {
      ored_conditions.push(conditions[index]);
      index += 1;
    } else {
      throw new Error("Unprocessable OR.");
    }
  }
  return ored_conditions;
}

// Parse an expression into a single Condition function.
function parse_expression(tokens) {
  let conditions = [];
  let index = 0;
  while (index < tokens.length) {
    console.log("Conditions:", conditions);
    console.log("Token index:", index);
    // Accounts for AND/OR/NOT.
    if (tokens[index] in Combiner) {
      conditions.push(tokens[index]);
      index += 1;
      continue;
    }
    // Accounts for parentheses.
    let [offset, condition] = parse_grouped_expression(tokens.slice(index));
    if (offset > 0 && condition !== null) {
      conditions.push(condition);
      index += offset;
      continue;
    }
    // Accounts for Facets, Operators, and Literals.
    [offset, condition] = parse_condition(tokens.slice(index));
    if (offset > 0 && condition !== null) {
      conditions.push(condition);
      index += offset;
      continue;
    }
    console.error(tokens[index]);
    throw new Error(`Unexpected token in expression: ${tokens[index]}`);
  }
  // Evaluate NOTs first, left to right.
  conditions = evaluate_not(conditions);
  // Evaluate ANDs second, left to right.
  conditions = evaluate_and(conditions);
  // Evaluate ORs third, left to right.
  conditions = evaluate_or(conditions);
  // Verify we have collapsed down to a single condition at this point.
  if (conditions.length !== 1 || !(conditions[0] instanceof Condition)) {
    throw new Error("Collapse should produce a single Condition.");
  }
  return conditions[0];
}

// Parse the query, returning a comparison function.
function query2condition(query) {
  const tokens = lexer(query);
  console.log("Tokens:", tokens);
  if (tokens.length === 0) {
    // If query is empty show everything.
    return new Condition((_) => true);
  }
  return parse_expression(tokens);
}

/**
 * End of query parser.
 */

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
      "description-container",
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

  // Create card for diagnostic.
  const facets = document.createElement("dl");
  for (const facet in record) {
    if (facet !== "title" && facet !== "path") {
      const facet_node = document.createElement("div");
      const facet_name = document.createElement("dt");
      const facet_value = document.createElement("dd");
      facet_name.textContent = facet;
      facet_value.textContent = record[facet];
      facet_node.append(facet_name, facet_value);
      facets.append(facet_node);
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
      if (position === "popup") {
        window.open(`${PLOTS_PATH}/${path}`, "_blank", "popup,width=800,height=600");
        return;
      }
      // Set the appropriate frame layout.
      position === "full" ? ensure_single_frame() : ensure_dual_frame();
      document.getElementById(`plot-frame-${position}`).src = `${PLOTS_PATH}/${path}`;
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
  if (value === "") {
    // Facet unselected, remove from query.
    new_query = query.replace(pattern, "");
  } else if (pattern.test(query)) {
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
  fetch(`${PLOTS_PATH}/index.jsonl`)
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
    for (const select of document.querySelectorAll("#filter-facets select")) {
      select.value = "";
    }
    doSearch();
  });
}

// Filter the displayed diagnostics by the query.
function doSearch() {
  const queryElem = document.getElementById("filter-query");
  const query = queryElem.value;
  // Update URL in address bar to match current query, deleting if blank.
  const url = new URL(document.location.href);
  query ? url.searchParams.set("q", query) : url.searchParams.delete("q");
  // Updates the URL without reloading the page.
  history.pushState(history.state, "", url.href);

  console.log("Search query:", query);
  let condition;
  try {
    condition = query2condition(query);
    // Set to an empty string to mark as valid.
    queryElem.setCustomValidity("");
  } catch (error) {
    console.error("Query failed to parse.", error);
    // Add :invalid pseudoclass to input, so user gets feedback.
    queryElem.setCustomValidity("Query failed to parse.");
    return;
  }

  // Filter all entries.
  for (const entryElem of document.querySelectorAll("#diagnostics > li")) {
    const entry = {};
    entry["title"] = entryElem.querySelector("h2").textContent;
    for (const facet_node of entryElem.querySelector("dl").children) {
      const facet = facet_node.firstChild.textContent;
      const value = facet_node.lastChild.textContent;
      entry[facet] = value;
    }

    // Show entries matching filter and hide entries that don't.
    if (condition.test(entry)) {
      entryElem.classList.remove("hidden");
    } else {
      entryElem.classList.add("hidden");
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
  if (e.data === " ") {
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
