export namespace main {
	
	export class FileItem {
	    id: number;
	    name: string;
	    ix: number;
	
	    static createFrom(source: any = {}) {
	        return new FileItem(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.ix = source["ix"];
	    }
	}
	export class Settings {
	    shuffleSeed: number;
	    dbFileName: string;
	    picDir: string;
	    replacePattern: string;
	    replaceWith: string;
	    findType: string;
	    findFrom: string;
	    findTo: string;
	    switchSeconds: number;
	    showId: boolean;
	    showSeq: boolean;
	    showName: boolean;
	    currentIndex: number;
	
	    static createFrom(source: any = {}) {
	        return new Settings(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.shuffleSeed = source["shuffleSeed"];
	        this.dbFileName = source["dbFileName"];
	        this.picDir = source["picDir"];
	        this.replacePattern = source["replacePattern"];
	        this.replaceWith = source["replaceWith"];
	        this.findType = source["findType"];
	        this.findFrom = source["findFrom"];
	        this.findTo = source["findTo"];
	        this.switchSeconds = source["switchSeconds"];
	        this.showId = source["showId"];
	        this.showSeq = source["showSeq"];
	        this.showName = source["showName"];
	        this.currentIndex = source["currentIndex"];
	    }
	}

}

