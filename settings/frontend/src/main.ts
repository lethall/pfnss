import './style.css';
import './app.css';
import './bootstrap.min.css';
import './bootstrap.bundle.min.js';

import { LoadImage, DoKey, SaveSettings, GetSettings, GetProjectFile, GetPicDir } from '../wailsjs/go/main/App';
import { EventsOn } from '../wailsjs/runtime';
import { main } from '../wailsjs/go/models';

let settings: main.Settings;

const keyCatcher = document.getElementById('keycatcher') as HTMLInputElement;

const loadImage = () => {
    try {
        LoadImage()
            .then((fileItem) => {
                if (fileItem.name == "") {
                    configure(true);
                    return;
                }
                const spans = (document.getElementById('photo-name') as HTMLDivElement).children;
                let id = spans?.item(0); // aka #accounce
                if (id) id.innerHTML = fileItem.mark;
                id = spans?.item(1);
                if (id) {
                    if (settings.showId) {
                        id.classList.remove("d-none");
                        id.innerHTML = `${fileItem.id}`;
                    } else {
                        id.classList.add("d-none");
                    }
                }
                id = spans?.item(2);
                if (id) {
                    if (settings.showName) {
                        id.classList.remove("d-none");
                        id.innerHTML = `${fileItem.name}`;
                    } else {
                        id.classList.add("d-none");
                    }
                }
                id = spans?.item(3);
                if (id) {
                    if (settings.showSeq) {
                        id.classList.remove("d-none");
                        id.innerHTML = `${fileItem.ix}`;
                    } else {
                        id.classList.add("d-none");
                    }
                }
                const viewer = document.getElementById('viewer') as HTMLDivElement;
                viewer.setAttribute("style", "background-image: url('" + fileItem.name + "')");
                keyCatcher.focus();
            })
            .catch((err) => {
                console.error(err);
            });
    } catch (err) {
        console.error(err);
    }
}

const doKey = function (ev: KeyboardEvent) {
    if (document.getElementById('viewer')?.classList.contains("d-none")) return;
    keyCatcher.value = "";
    ev.preventDefault();
    DoKey(ev.key);
}

keyCatcher.focus();
keyCatcher.addEventListener("keyup", doKey);

const announce = function (s: string) {
    (document.getElementById('announce') as HTMLSpanElement).innerHTML = s;
}

const configure = (showForm: boolean): Promise<void> => {
    GetSettings()
        .then((currentSettings) => {
            settings = currentSettings;
            (document.getElementById("shuffleSeed") as HTMLInputElement).valueAsNumber = settings.shuffleSeed;
            (document.getElementById("replacePattern") as HTMLInputElement).value = settings.replacePattern;
            (document.getElementById("replaceWith") as HTMLInputElement).value = settings.replaceWith;
            (document.getElementById("showTimer") as HTMLInputElement).valueAsNumber = settings.switchSeconds;
            (document.getElementById("dbFileName") as HTMLSpanElement).innerHTML = settings.dbFileName;
            (document.getElementById("picDir") as HTMLSpanElement).innerHTML = settings.picDir;
            (document.getElementById("showId") as HTMLInputElement).checked = settings.showId;
            (document.getElementById("showSeq") as HTMLInputElement).checked = settings.showSeq;
            (document.getElementById("showName") as HTMLInputElement).checked = settings.showName;
            (document.getElementById("findType") as HTMLSelectElement).value = settings.findType;
            (document.getElementById("findFrom") as HTMLInputElement).value = settings.findFrom;
            (document.getElementById("findTo") as HTMLInputElement).value = settings.findTo;

            changeFindType(settings.findType);

            if (showForm) {
                document.getElementById('viewer')?.classList.add("d-none");
                document.getElementById('configure')?.classList.remove("d-none");
            }
        }
        ).catch((err) => {
            console.error(err);
        });
    return Promise.resolve();
}

const view = () => {
    document.getElementById('configure')?.classList.add("d-none");
    document.getElementById('viewer')?.classList.remove("d-none");
    DoKey("!")
}

const saveSettings = (doSave: boolean) => {
    if (doSave) {
        settings.shuffleSeed = (document.getElementById("shuffleSeed") as HTMLInputElement).valueAsNumber;
        settings.replacePattern = (document.getElementById("replacePattern") as HTMLInputElement).value;
        settings.replaceWith = (document.getElementById("replaceWith") as HTMLInputElement).value;
        settings.switchSeconds = (document.getElementById("showTimer") as HTMLInputElement).valueAsNumber;
        settings.dbFileName = (document.getElementById("dbFileName") as HTMLSpanElement).innerHTML;
        settings.picDir = (document.getElementById("picDir") as HTMLSpanElement).innerHTML;
        settings.showId = (document.getElementById("showId") as HTMLInputElement).checked;
        settings.showSeq = (document.getElementById("showSeq") as HTMLInputElement).checked;
        settings.showName = (document.getElementById("showName") as HTMLInputElement).checked;
        settings.findType = (document.getElementById("findType") as HTMLSelectElement).value;
        settings.findFrom = (document.getElementById("findFrom") as HTMLInputElement).value;
        settings.findTo = (document.getElementById("findTo") as HTMLInputElement).value;
    }

    SaveSettings(settings);
    view();
}

const getProjectFile = (ev: MouseEvent) => {
    ev.preventDefault();
    ev.stopPropagation();
    try {
        GetProjectFile()
            .then((fileName) => {
                (document.getElementById('dbFileName') as HTMLSpanElement).innerHTML = fileName;
            })
            .catch((err) => {
                console.error(err);
            });

    } catch (err) {
        console.error(err);
    }
}

const getPicDir = (ev: MouseEvent) => {
    ev.preventDefault();
    ev.stopPropagation();
    try {
        GetPicDir()
            .then((picDir) => {
                (document.getElementById('picDir') as HTMLSpanElement).innerHTML = picDir;
            })
            .catch((err) => {
                console.error(err);
            });

    } catch (err) {
        console.error(err);
    }
}

const applyClass = (items: HTMLCollection, classNme: string, add: Boolean) => {
    for (var ii = 0; ii < items.length; ++ii) {
        const item = items[ii] as HTMLDivElement;
        if (add) {
            item.classList.add(classNme);
        } else {
            item.classList.remove(classNme);
        }
    }
}

const changeFindType = (findType: string) => {
    const findFrom = document.getElementById('findFrom') as HTMLInputElement;
    const findTo = document.getElementById('findTo') as HTMLInputElement;
    let findByFromLabel = "";
    let findByToLabel = "";
    if (findType == "byAll") {
        findFrom.disabled = true;
        findTo.disabled = true;
        applyClass(document.getElementsByClassName('finders'), "d-none", true);
    } else {
        if (findType == "byShown") {
            findFrom.type = findTo.type = "datetime-local";
            findByFromLabel = "earliest time shown";
            findByToLabel = "latest time shown";
        } else {
            findFrom.type = findTo.type = "number";
            let typeLabel = (findType == "byId") ? "file ID number" : "sequence number";
            findByFromLabel = `lowest ${typeLabel}`;
            findByToLabel = `highest ${typeLabel}`;
        }
        (findFrom.nextElementSibling as HTMLDivElement).innerHTML = `Choose the ${findByFromLabel}`;
        (findTo.nextElementSibling as HTMLDivElement).innerHTML = `Choose the ${findByToLabel}`;
        findFrom.disabled = false;
        findTo.disabled = false;
        applyClass(document.getElementsByClassName('finders'), "d-none", false);
    }
}

document.getElementById('viewer')?.addEventListener("click", loadImage);
document.getElementById('cancel')?.addEventListener("click", () => { saveSettings(false); });
document.getElementById('save')?.addEventListener("click", () => { saveSettings(true); });
document.getElementById('projectChooser')?.addEventListener("click", (ev) => { getProjectFile(ev); });
document.getElementById('picDirChooser')?.addEventListener("click", (ev) => { getPicDir(ev); });
document.getElementById('findType')?.addEventListener("change", (ev) => { changeFindType((ev.target as HTMLSelectElement).value); });
EventsOn("loadimage", () => { loadImage(); });
EventsOn("announce", (s: string) => { announce(s); });
EventsOn("configure", () => { configure(true); });

configure(false).then(() => { loadImage(); });
