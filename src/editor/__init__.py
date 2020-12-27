import re
from sublime import Region


class HTMLEditor:

    def __init__(self, view):
        self.new, self.edited, self.deleted = self._calculate(
            old=self._readlines(view),
            new=self._readregions(view)
        )

    def _calculate(self, old, new):
        new_lines = []
        edited = []
        deleted = []

        old_copy = [line.replace('\n', '') for line in old]
        new_copy = [line.replace('\n', '') for line in new]

        for i, line in enumerate(new_copy):
            if line not in old_copy:
                section = self._parse_id(line)
                if section:
                    edited.append((self._to_html(line), section))
                    continue
                if i <= len(old_copy):
                    section = self._parse_id(old_copy[i-1])
                new_lines.append((self._to_html(new[i]), section))

        edited_sections = [section for line,section in edited]
        for i, copy in enumerate(old_copy):
            if copy not in new_copy:
                section = self._parse_id(old[i])
                if section and section not in edited_sections:
                    deleted.append(section)
                old.remove(old[i])

        return new_lines, edited, deleted

    def _readlines(self, view):
        try:
            with open(view.file_name()) as file:
                return [line for line in file.readlines() if line and line != '\n']
        except Exception as ex:
            print(ex)
        return []

    def _readregions(self, view):
        lines = []
        for region in view.lines(Region(0, view.size())):
            text = view.substr(region)
            if text and text != '\n':
                lines.append(text)
        return lines

    def _get_sections(self, lines):
        return set([self._parse_id(line) for line in lines])

    def _parse_id(self, line):
        if line:
            result = re.search(r"id='\w{11}'", line)
            if result:
                id = result.group(0).split("'")[-2]
                if len(id) == 11:
                    return id

    def _to_html(self, line):
        if line.startswith('<') and (line.endswith('>') or line.endswith('>\n')):
            return line
        return "<p>" + line + "</p>"