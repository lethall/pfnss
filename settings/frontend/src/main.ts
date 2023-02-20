import './style.css';
import './app.css';

import {LoadImage} from '../wailsjs/go/main/App';

window.loadImage = function () {
    try {
        LoadImage(seq)
            .then((fileName) => {
                const app = document.getElementById('app') as HTMLDivElement;
                app.innerText = fileName;
                app.setAttribute("style", "background-image: url('" + fileName + "')");
                seq++
            })
            .catch((err) => {
                console.error(err);
            });
    } catch (err) {
        console.error(err);
    }
};

declare global {
    interface Window {
        loadImage: () => void;
    }
}

let seq = 0;
window.loadImage();
