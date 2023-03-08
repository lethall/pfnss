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
	    dbFileName: string;
	    absPrefix: string;
	    switchSeconds: number;
	    shuffleSeed: number;
	
	    static createFrom(source: any = {}) {
	        return new Settings(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.dbFileName = source["dbFileName"];
	        this.absPrefix = source["absPrefix"];
	        this.switchSeconds = source["switchSeconds"];
	        this.shuffleSeed = source["shuffleSeed"];
	    }
	}

}

