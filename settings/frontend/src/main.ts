import './style.css';
import './app.css';
import './bootstrap.min.css';
import './bootstrap.bundle.min.js';

import { LoadImage, DoKey, SaveSettings, GetSettings, GetProjectFile, GetPicDir } from '../wailsjs/go/main/App';
import { EventsOn } from '../wailsjs/runtime';
import { main } from '../wailsjs/go/models';

declare global {
    interface Window {
        loadImage: () => void;
        doKey: (ev: KeyboardEvent) => void;
        announce: (s: string) => void;
        getImage: (n: number) => void;
        configure: (showForm: boolean, nextOp: any) => void;
        saveSettings: () => void;
        getProjectFile: (ev: MouseEvent) => void;
        getPicDir: (ev: MouseEvent) => void;
        changeFindType: (findType: string) => void;
        applyClass: (items: HTMLCollection, className: string, add: Boolean) => void;
        view: () => void;
        settings: main.Settings;
    }
}

window.loadImage = () => {
    try {
        LoadImage(seq)
            .then((fileItem) => {
                if (fileItem.name == "") {
                    window.configure(true, null);
                    return;
                }
                seq = fileItem.ix;
                const spans = (document.getElementById('photo-name') as HTMLDivElement).children;
                let id = spans?.item(0); // aka #accounce
                if (id) id.innerHTML = '';
                id = spans?.item(1);
                if (id) {
                    if (window.settings.showId) {
                        id.classList.remove("d-none");
                        id.innerHTML = `${fileItem.id}`;
                    } else {
                        id.classList.add("d-none");
                    }
                }
                id = spans?.item(2);
                if (id) {
                    if (window.settings.showName) {
                        id.classList.remove("d-none");
                        id.innerHTML = `${fileItem.name}`;
                    } else {
                        id.classList.add("d-none");
                    }
                }
                id = spans?.item(3);
                if (id) {
                    if (window.settings.showSeq) {
                        id.classList.remove("d-none");
                        id.innerHTML = `${seq}`;
                    } else {
                        id.classList.add("d-none");
                    }
                }
                (document.getElementById('viewer') as HTMLDivElement).setAttribute("style", "background-image: url('" + fileItem.name + "')");
                seq++
            })
            .catch((err) => {
                console.error(err);
            });
    } catch (err) {
        console.error(err);
    }
};

window.getImage = function (n: number) {
    seq = n;
    window.loadImage();
}

window.doKey = function (ev: KeyboardEvent) {
    if (document.getElementById('viewer')?.classList.contains("d-none")) return;
    ev.preventDefault();
    DoKey(ev.key);
}



window.announce = function (s: string) {
    (document.getElementById('announce') as HTMLSpanElement).innerHTML = s;
}

window.configure = (showForm: boolean, nextOp: any) => {
    GetSettings()
        .then((currentSettings) => {
            window.settings = currentSettings;
            (document.getElementById("shuffleSeed") as HTMLInputElement).valueAsNumber = window.settings.shuffleSeed;
            (document.getElementById("replacePattern") as HTMLInputElement).value = window.settings.replacePattern;
            (document.getElementById("replaceWith") as HTMLInputElement).value = window.settings.replaceWith;
            (document.getElementById("showTimer") as HTMLInputElement).valueAsNumber = window.settings.switchSeconds;
            (document.getElementById("dbFileName") as HTMLSpanElement).innerHTML = window.settings.dbFileName;
            (document.getElementById("picDir") as HTMLSpanElement).innerHTML = window.settings.picDir;
            (document.getElementById("showId") as HTMLInputElement).checked = window.settings.showId;
            (document.getElementById("showSeq") as HTMLInputElement).checked = window.settings.showSeq;
            (document.getElementById("showName") as HTMLInputElement).checked = window.settings.showName;
            (document.getElementById("findType") as HTMLSelectElement).value = window.settings.findType;
            (document.getElementById("findFrom") as HTMLInputElement).value = window.settings.findFrom;
            (document.getElementById("findTo") as HTMLInputElement).value = window.settings.findTo;

            window.changeFindType(window.settings.findType);
            seq = window.settings.currentIndex;

            if (showForm) {
                document.getElementById('viewer')?.classList.add("d-none");
                document.getElementById('configure')?.classList.remove("d-none");
            }

            if (nextOp) nextOp();
        }
        ).catch((err) => {
            console.error(err);
        });
}

window.view = () => {
    document.getElementById('configure')?.classList.add("d-none");
    document.getElementById('viewer')?.classList.remove("d-none");
    DoKey("!")
}

window.saveSettings = () => {
    window.settings.shuffleSeed = (document.getElementById("shuffleSeed") as HTMLInputElement).valueAsNumber;
    window.settings.replacePattern = (document.getElementById("replacePattern") as HTMLInputElement).value;
    window.settings.replaceWith = (document.getElementById("replaceWith") as HTMLInputElement).value;
    window.settings.switchSeconds = (document.getElementById("showTimer") as HTMLInputElement).valueAsNumber;
    window.settings.dbFileName = (document.getElementById("dbFileName") as HTMLSpanElement).innerHTML;
    window.settings.picDir = (document.getElementById("picDir") as HTMLSpanElement).innerHTML;
    window.settings.showId = (document.getElementById("showId") as HTMLInputElement).checked;
    window.settings.showSeq = (document.getElementById("showSeq") as HTMLInputElement).checked;
    window.settings.showName = (document.getElementById("showName") as HTMLInputElement).checked;
    window.settings.findType = (document.getElementById("findType") as HTMLSelectElement).value;
    window.settings.findFrom = (document.getElementById("findFrom") as HTMLInputElement).value;
    window.settings.findTo = (document.getElementById("findTo") as HTMLInputElement).value;

    SaveSettings(window.settings);
    window.view();
}

window.getProjectFile = (ev: MouseEvent) => {
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

window.getPicDir = (ev: MouseEvent) => {
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

window.applyClass = (items: HTMLCollection, classNme: string, add: Boolean) => {
    for (var ii = 0; ii < items.length; ++ii) {
        const item = items[ii] as HTMLDivElement;
        if (add) {
            item.classList.add(classNme);
        } else {
            item.classList.remove(classNme);
        }
    }
}

window.changeFindType = (findType: string) => {
    if (findType == "byAll") {
        (document.getElementById('findFrom') as HTMLInputElement).disabled = true;
        (document.getElementById('findTo') as HTMLInputElement).disabled = true;
        window.applyClass(document.getElementsByClassName('finders'), "d-none", true);
    } else {
        (document.getElementById('findFrom') as HTMLInputElement).disabled = false;
        (document.getElementById('findTo') as HTMLInputElement).disabled = false;
        window.applyClass(document.getElementsByClassName('finders'), "d-none", false);
    }
}

document.getElementById('viewer')?.addEventListener("click", window.loadImage);
document.getElementById('cancel')?.addEventListener("click", window.view);
document.getElementById('save')?.addEventListener("click", window.saveSettings);
document.getElementById('projectChooser')?.addEventListener("click", (ev) => { window.getProjectFile(ev); });
document.getElementById('picDirChooser')?.addEventListener("click", (ev) => { window.getPicDir(ev); });
document.getElementById('findType')?.addEventListener("change", (ev) => { window.changeFindType((ev.target as HTMLSelectElement).value); });
document.addEventListener("keyup", window.doKey);
EventsOn("loadimage", (d: number) => { window.getImage(d); })
EventsOn("announce", (s: string) => { window.announce(s); })
EventsOn("configure", () => { window.configure(true, null); })

let seq = 0;
window.configure(false, window.loadImage);
