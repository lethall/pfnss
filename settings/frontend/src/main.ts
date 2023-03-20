import './style.css';
import './app.css';
import './bootstrap.min.css';
import './bootstrap.bundle.min.js';

import { LoadImage, DoKey, SaveSettings, GetProjectFile } from '../wailsjs/go/main/App';
import { EventsOn } from '../wailsjs/runtime';
import { main } from '../wailsjs/go/models';

declare global {
    interface Window {
        loadImage: () => void;
        doKey: (ev: KeyboardEvent) => void;
        announce: (s: string) => void;
        getImage: (n: number) => void;
        configure: () => void;
        saveSettings: () => void;
        getProjectFile: (ev: MouseEvent) => void;
        view: () => void;
    }
}

window.loadImage = function () {
    try {
        LoadImage(seq)
            .then((fileItem) => {
                seq = fileItem.ix;
                const spans = (document.getElementById('photo-name') as HTMLDivElement).children;
                let id = spans?.item(0); // aka #accounce
                if (id) id.innerHTML = '';
                id = spans?.item(1);
                if (id) id.innerHTML = `${fileItem.id}`;
                id = spans?.item(2);
                if (id) id.innerHTML = `${fileItem.name}`;
                id = spans?.item(3);
                if (id) id.innerHTML = `${seq}`;
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

window.configure = function () {
    document.getElementById('viewer')?.classList.add("d-none");
    document.getElementById('configure')?.classList.remove("d-none");
}

window.view = function () {
    document.getElementById('configure')?.classList.add("d-none");
    document.getElementById('viewer')?.classList.remove("d-none");
    DoKey(" ")
}

window.saveSettings = function () {
    const settings: main.Settings = {
        dbFileName: "filename",
        absPrefix: "prefix",
        shuffleSeed: 123,
        switchSeconds: 10
    };
    SaveSettings(settings);
    window.view();
}

window.getProjectFile = function (ev: MouseEvent) {
    ev.preventDefault();
    ev.stopPropagation();
    try {
        GetProjectFile()
            .then((fileName) => {
                const projectFileName = document.getElementById('projectFileName') as HTMLSpanElement;
                projectFileName.innerHTML = fileName;
            })
            .catch((err) => {
                console.error(err);
            });

    } catch (err) {
        console.error(err);
    }
}

document.getElementById('viewer')?.addEventListener("click", window.loadImage);
document.getElementById('cancel')?.addEventListener("click", window.view);
document.getElementById('save')?.addEventListener("click", window.saveSettings);
document.getElementById('projectChooser')?.addEventListener("click", (ev) => {
    window.getProjectFile(ev);
});
document.addEventListener("keyup", window.doKey);
EventsOn("loadimage", (d: number) => { window.getImage(d); })
EventsOn("announce", (s: string) => { window.announce(s); })
EventsOn("configure", () => { window.configure(); })

let seq = 0;

window.loadImage();
// window.configure();
