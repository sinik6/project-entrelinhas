// Avatar de uma pessoa (spec 004, REQ-7.8): a foto, ou a inicial do nome sobre a cor dela quando não há foto ou ela não carrega.
import 'package:entrelinhas/shared/ui/cores.dart';
import 'package:flutter/material.dart';

/// Base da API, a mesma do cliente HTTP; o endereço da foto vem relativo a ela.
const _baseDaApi = String.fromEnvironment('API_BASE', defaultValue: '/api/v1');

String urlDaFoto(String relativa) => '$_baseDaApi/$relativa';

/// Preto ou branco, o que tiver mais contraste com a cor de fundo.
Color corDaInicial(Color fundo) {
  final luz = fundo.computeLuminance();
  final contrasteComBranco = 1.05 / (luz + 0.05);
  final contrasteComPreto = (luz + 0.05) / 0.05;
  return contrasteComBranco >= contrasteComPreto ? Colors.white : Colors.black;
}

class Avatar extends StatelessWidget {
  const Avatar({
    required this.nome,
    required this.cor,
    this.fotoUrl,
    this.tamanho = 40,
    super.key,
  });

  final String nome;
  final String cor;
  final String? fotoUrl;
  final double tamanho;

  @override
  Widget build(BuildContext context) {
    final fundo = corDeTexto(cor);
    final inicial = Center(
      child: Text(
        nome.trim().isEmpty ? '?' : nome.trim().substring(0, 1).toUpperCase(),
        style: TextStyle(
          color: corDaInicial(fundo),
          fontSize: tamanho * 0.45,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
    final url = fotoUrl;
    return Semantics(
      image: true,
      label: url == null ? 'Sem foto de $nome' : 'Foto de $nome',
      excludeSemantics: true,
      child: Container(
        width: tamanho,
        height: tamanho,
        clipBehavior: Clip.antiAlias,
        decoration: BoxDecoration(color: fundo, shape: BoxShape.circle),
        child: url == null
            ? inicial
            : Image.network(
                urlDaFoto(url),
                width: tamanho,
                height: tamanho,
                fit: BoxFit.cover,
                errorBuilder: (_, _, _) => inicial,
              ),
      ),
    );
  }
}
