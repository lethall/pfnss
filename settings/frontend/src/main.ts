import './style.css';
import './app.css';

import {LoadImage, DoKey} from '../wailsjs/go/main/App';

declare global {
    interface Window {
        loadImage: () => void;
        doKey: (ev: KeyboardEvent) => void;
    }
}

window.loadImage = function () {
    try {
        LoadImage(seq)
            .then((fileItem) => {
                const app = document.getElementById('app') as HTMLDivElement;
                app.innerText = fileItem.name;
                app.setAttribute("style", "background-image: url('" + fileItem.name + "')");
                seq++
            })
            .catch((err) => {
                console.error(err);
            });
    } catch (err) {
        console.error(err);
    }
};

window.doKey = function (ev: KeyboardEvent) {
    ev.preventDefault();
    DoKey(ev.key)
}

let seq = 0;
window.loadImage();
