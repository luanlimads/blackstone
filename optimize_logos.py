"""
Otimiza as logos da Black Stone:
1. Remove fundo branco (converte branco/quase-branco para transparente)
2. Autocrop (remove espaço vazio ao redor)
3. Salva em PNG com transparência
4. Cria versões para header (logotipo texto) e footer (logo completa)
5. Cria versão branca do logotipo para uso no footer escuro
"""

from PIL import Image, ImageFilter
import numpy as np
import sys
import os


def remove_white_background(img, threshold=240, edge_smoothing=True):
    """Remove fundo branco mantendo anti-aliasing nas bordas."""
    img = img.convert('RGBA')
    data = np.array(img)

    # Detectar pixels brancos/quase-brancos
    r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]

    # Máscara: pixels onde R, G e B estão todos acima do threshold
    white_mask = (r > threshold) & (g > threshold) & (b > threshold)

    # Para anti-aliasing: pixels próximos ao branco ganham alpha proporcional
    # Quanto mais branco, mais transparente
    brightness = (r.astype(float) + g.astype(float) + b.astype(float)) / 3.0

    # Criar gradiente de transparência para bordas suaves
    soft_threshold = threshold - 40  # zona de transição
    alpha_new = np.where(
        white_mask,
        0,  # totalmente branco = totalmente transparente
        np.where(
            brightness > soft_threshold,
            # Zona de transição: alpha proporcional
            ((threshold - brightness) / (threshold - soft_threshold) * 255).clip(0, 255),
            a  # manter alpha original para pixels escuros
        )
    ).astype(np.uint8)

    data[:, :, 3] = alpha_new
    result = Image.fromarray(data)
    return result


def autocrop(img, padding=10):
    """Remove espaço vazio (transparente) ao redor da imagem."""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Encontrar bbox dos pixels não-transparentes
    alpha = np.array(img)[:, :, 3]
    rows = np.any(alpha > 10, axis=1)
    cols = np.any(alpha > 10, axis=0)

    if not rows.any() or not cols.any():
        return img

    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    # Adicionar padding
    rmin = max(0, rmin - padding)
    rmax = min(img.height - 1, rmax + padding)
    cmin = max(0, cmin - padding)
    cmax = min(img.width - 1, cmax + padding)

    return img.crop((cmin, rmin, cmax + 1, rmax + 1))


def make_white_version(img):
    """Converte todos os pixels não-transparentes para branco (para footer escuro)."""
    img = img.convert('RGBA')
    data = np.array(img)

    # Onde alpha > 0, converter para branco mantendo o alpha
    mask = data[:, :, 3] > 0
    data[:, :, 0] = np.where(mask, 255, data[:, :, 0])
    data[:, :, 1] = np.where(mask, 255, data[:, :, 1])
    data[:, :, 2] = np.where(mask, 255, data[:, :, 2])

    return Image.fromarray(data)


def process_logo(input_path, output_path, max_height=None, make_white=False):
    """Pipeline completa de otimização."""
    print(f"  Abrindo: {input_path}")
    img = Image.open(input_path)
    print(f"  Tamanho original: {img.size}")

    # 1. Remover fundo branco
    print("  Removendo fundo branco...")
    img = remove_white_background(img, threshold=245)

    # 2. Autocrop
    print("  Fazendo autocrop...")
    img = autocrop(img, padding=5)
    print(f"  Tamanho após crop: {img.size}")

    # 3. Versão branca se necessário
    if make_white:
        print("  Convertendo para branco...")
        img = make_white_version(img)

    # 4. Redimensionar se necessário (manter aspect ratio)
    if max_height and img.height > max_height:
        ratio = max_height / img.height
        new_width = int(img.width * ratio)
        img = img.resize((new_width, max_height), Image.LANCZOS)
        print(f"  Redimensionado para: {img.size}")

    # 5. Salvar
    img.save(output_path, 'PNG', optimize=True)
    file_size = os.path.getsize(output_path)
    print(f"  ✓ Salvo: {output_path} ({file_size / 1024:.1f} KB)")
    return img


def main():
    img_dir = os.path.join(os.path.dirname(__file__), 'img')

    print("=" * 60)
    print("BLACK STONE — Otimização de Logos")
    print("=" * 60)

    # Verificar quais arquivos de logo existem
    logo_completa = os.path.join(img_dir, 'logo-original-completa.png')
    logotipo_texto = os.path.join(img_dir, 'logo-original-texto.png')

    # Fallback para arquivos existentes
    if not os.path.exists(logo_completa):
        logo_completa = os.path.join(img_dir, 'logo.png')
    if not os.path.exists(logotipo_texto):
        logotipo_texto = os.path.join(img_dir, 'logo-blackstone-transparent.png')

    results = []

    # === PROCESSAR LOGOTIPO TEXTO (para o header) ===
    if os.path.exists(logotipo_texto):
        print(f"\n{'─' * 40}")
        print("1. LOGOTIPO TEXTO → Header")
        print(f"{'─' * 40}")
        process_logo(
            logotipo_texto,
            os.path.join(img_dir, 'logo-header.png'),
            max_height=200  # Alta resolução, CSS controla o tamanho
        )
        results.append('logo-header.png')

        # Versão branca para footer
        print(f"\n{'─' * 40}")
        print("2. LOGOTIPO TEXTO BRANCO → Footer")
        print(f"{'─' * 40}")
        process_logo(
            logotipo_texto,
            os.path.join(img_dir, 'logo-footer-white.png'),
            max_height=200,
            make_white=True
        )
        results.append('logo-footer-white.png')
    else:
        print(f"\n⚠ Logotipo texto não encontrado em: {logotipo_texto}")

    # === PROCESSAR LOGO COMPLETA (símbolo + texto) ===
    if os.path.exists(logo_completa):
        print(f"\n{'─' * 40}")
        print("3. LOGO COMPLETA → Versão alternativa")
        print(f"{'─' * 40}")
        process_logo(
            logo_completa,
            os.path.join(img_dir, 'logo-completa.png'),
            max_height=400
        )
        results.append('logo-completa.png')

        # Versão branca
        print(f"\n{'─' * 40}")
        print("4. LOGO COMPLETA BRANCA → Footer alternativo")
        print(f"{'─' * 40}")
        process_logo(
            logo_completa,
            os.path.join(img_dir, 'logo-completa-white.png'),
            max_height=400,
            make_white=True
        )
        results.append('logo-completa-white.png')
    else:
        print(f"\n⚠ Logo completa não encontrada em: {logo_completa}")

    print(f"\n{'=' * 60}")
    print(f"✓ {len(results)} arquivo(s) gerado(s):")
    for r in results:
        print(f"  → img/{r}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
