from typing import List


class ResumeChunkService:

    def create_chunks(self, resume_data) -> List[dict]:

        chunks = []

        if resume_data.summary:
            chunks.append(
                {
                    "chunk_id": f"{resume_data.id}_summary",
                    "chunk_type": "summary",
                    "content": f"""
Summary

{resume_data.summary}
""".strip(),
                }
            )

        if resume_data.skills:

            skills_list = ", ".join(
                skill.skill_name
                for skill in resume_data.skills
            )

            chunks.append(
                {
                    "chunk_id": f"{resume_data.id}_skills",
                    "chunk_type": "skills",
                    "content": f"""
Skills

{skills_list}
""".strip(),
                }
            )

        return chunks


resume_chunk_service = ResumeChunkService()