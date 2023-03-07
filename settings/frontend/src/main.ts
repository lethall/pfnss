import './style.css';
import './app.css';
import './bootstrap.min.css';
import './bootstrap.bundle.min.js';

import {LoadImage, DoKey} from '../wailsjs/go/main/App';
import {EventsOn} from '../wailsjs/runtime'

declare global {
    interface Window {
        loadImage: () => void;
        doKey: (ev: KeyboardEvent) => void;
        announce: (s: string) => void;
        getImage: (n: number) => void;
        configure: () => void;
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

document.getElementById('viewer')?.addEventListener("click", window.loadImage);
document.addEventListener("keyup", window.doKey);
EventsOn("loadimage", (d: number) => { window.getImage(d); })
EventsOn("announce", (s: string) => { window.announce(s); })
EventsOn("configure", () => { window.configure(); })

let seq = 0;

window.loadImage();
