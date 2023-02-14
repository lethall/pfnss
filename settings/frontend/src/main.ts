import './style.css';
import './app.css';

import logo from './assets/images/samson.jpg';
import {LoadImage} from '../wailsjs/go/main/App';
import {WindowReload} from '../wailsjs/runtime/runtime';

window.loadImage = function () {
    // ev.preventDefault();
    try {
        LoadImage()
            .then((result) => {
                imageInfo!.innerText = result;
                (document.getElementById('logo') as HTMLImageElement).src = result;
                // WindowReload();
            })
            .catch((err) => {
                console.error(err);
            });
    } catch (err) {
        console.error(err);
    }
};

document.querySelector('#app')!.innerHTML = `
    <img id="logo" class="logo">
    <button onclick="loadImage()">Next image</button>
    <p id="imageInfo"></p>
`;
(document.getElementById('logo') as HTMLImageElement).src = logo;

let imageInfo = document.getElementById("imageInfo");

declare global {
    interface Window {
        loadImage: () => void;
    }
}
