import './style.css';
import './app.css';

import {LoadImage, DoKey} from '../wailsjs/go/main/App';
import {EventsOn} from '../wailsjs/runtime'

declare global {
    interface Window {
        loadImage: () => void;
        doKey: (ev: KeyboardEvent) => void;
        getImage: (n: number) => void;
    }
}

window.loadImage = function () {
    try {
        LoadImage(seq)
            .then((fileItem) => {
                const spans = (document.getElementById('photo-name') as HTMLDivElement).children;
                let id = spans?.item(0);
                if (id) id.innerHTML = `${fileItem.id}`;
                id = spans?.item(1);
                if (id) id.innerHTML = `${fileItem.name}`;
                id = spans?.item(2);
                if (id) id.innerHTML = `${seq}`;
                (document.getElementById('app') as HTMLDivElement).setAttribute("style", "background-image: url('" + fileItem.name + "')");
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
    ev.preventDefault();
    DoKey(ev.key)
}

document.addEventListener("keyup", window.doKey);
EventsOn("loadimage", (d: number) => { window.getImage(d); })

let seq = 0;

window.loadImage();
