"use strict";

function update_displayed_plot(event) {
    const plot_url = plot_urls[event.srcElement.value - 1];
    show_plot(plot_url);
}

function show_plot(url) {
    // Retrieve a plot from the tarball and put it on the canvas
    const canvas = document.querySelector("#plot");
    const ctx = canvas.getContext("2d")
    ctx.reset()

    getBlobFromTar(url)
        .then(createImageBitmap)
        .then((img) => {
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);
        });
}

function display_sequence_controls(plot_urls) {
    // Only show sequence controls if there are multiple plots.
    if (plot_urls == undefined || plot_urls.length < 2) {
        return;
    }

    // Enable sequence controls.
    const sequence_controls = document.querySelector("#sequence_controls");
    sequence_controls.classList.remove("hidden")

    // Wire up the controls.
    const sequence_range = document.querySelector("#sequence_range");
    sequence_range.max = plot_urls.length;
    sequence_range.addEventListener("input", () => {
        sequence_number.value = sequence_range.value;
    });
    sequence_range.addEventListener("input", update_displayed_plot);

    const sequence_number = document.querySelector("#sequence_number");
    sequence_number.max = plot_urls.length;
    sequence_number.addEventListener("input", () => {
        sequence_range.value = sequence_number.value;
    });
    sequence_number.addEventListener("change", update_displayed_plot);
}

let tar_index = null;
async function getFromTar(path) {
    // Tarfile to load
    const tarfile = 'plots.tar';
    const key = path;

    // Tarfile index
    if (tar_index === null) {
        const r = await(fetch('tarindex.json'));
        tar_index = await r.json();
    }

    if (! (key in tar_index)) {
        console.log(key);
        throw 404;
    }

    const start = tar_index[key][0];
    const end = tar_index[key][1] - 1;

    const slice = await fetch(tarfile, {headers: {Range: `bytes=${start}-${end}`}, cache: 'default'});

    return slice
}

let tar_cache = {};
async function getBlobFromTar(path) {
    // Return a blob from the tarball, caching results
    if (path in tar_cache) {
        return tar_cache[path];
    }
    const slice = await getFromTar(path);
    tar_cache[path] = slice.blob();
    return tar_cache[path];
}

async function get_metadata() {
    // Retrieve the Json metadata for this plot directory from the tarball
    const meta = await getFromTar(`${path}/meta.json`);
    return meta.json();
}

let plot_urls = [];
function setup_plots(meta) {
    // Set up the plot using the metadata info
    document.getElementById("title").innerHTML = meta["title"];
    document.getElementById("desc-title").innerHTML = meta["title"];
    document.getElementById("desc-description").innerHTML = meta["description"];

    // Set up the plot URLs
    const plots = meta["plots"];
    plot_urls = plots.map((p) => `${path}/${p}`);

    display_sequence_controls(plot_urls);

    // Show the first plot
    show_plot(plot_urls[0]);
}

let path = "";
function setup() {
    // Get the path to the plot directory from the url then setup the page
    const searchParams = new URLSearchParams(window.location.search);
    path = searchParams.get("path");

    get_metadata().then(setup_plots);
}

document.addEventListener('DOMContentLoaded', setup);
