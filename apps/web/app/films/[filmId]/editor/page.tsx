import EditorClient from '../../../../components/editor/EditorClient';

interface Props {
  params: { filmId: string };
}

export default function EditorPage({ params }: Props) {
  return <EditorClient filmId={params.filmId} />;
}
