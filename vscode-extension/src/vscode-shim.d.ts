declare module 'vscode' {
  export class Position {
    constructor(public line: number, public character: number);
  }

  export class Range {
    constructor(
      public startLine: number,
      public startCharacter: number,
      public endLine: number,
      public endCharacter: number,
    );
    start: Position;
    end: Position;
  }

  export enum DiagnosticSeverity {
    Error = 0,
    Warning = 1,
    Information = 2,
    Hint = 3,
  }

  export class Diagnostic {
    constructor(public range: Range, public message: string, public severity: DiagnosticSeverity);
    source?: string;
    code?: string;
  }
}
